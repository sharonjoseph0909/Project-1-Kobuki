import rclpy
from rclpy.node import Node
from nav_msgs.msg import Odometry
from kobuki_ros_interfaces.msg import BumperEvent
from geometry_msgs.msg import Twist
from std_msgs.msg import Empty
from kobuki_ros_interfaces.msg import Led
import time
import sys

import math

class Odom(Node):
    def __init__(self):
        super().__init__('odom')
        
        self.subscription = self.create_subscription(Odometry, 'odom', self.odom_callback, 10)
        self.subscription
        
        #self.subscription = self.create_subscription(BumperEvent, '/events/bumper', self.bumper_callback, 10)
        #self.subscription
        
        self.pub_vel = self.create_publisher(Twist, '/cmd_vel', 10)
        
        self.pub_reset = self.create_publisher(Empty, '/commands/reset_odometry', 10)
        
        self.pubLed1 = self.create_publisher(Led, '/commands/led1', 1)
        self.pubLed2 = self.create_publisher(Led, '/commands/led2', 1)
        
        self.timer = self.create_timer(0.1, self.move_callback)
        self.timer = self.create_timer(0.25, self.led_callback)
        
        self.current_linear = 0.0
        self.current_angular = 0.0
        self.target_linear = 0.0
        self.target_linear_rev = 0.0
        self.target_angular = 0.0
        self.delta_linear = 0.05 #0.1
        self.delta_angular = 0.1 #0.2
        self.delta_brake_angular = 0.15 #0.25
        self.delta_brake_linear = 0.075
        
        self.max_speed_list = []
        self.target_linear_list = []
        self.target_angular_list = []
        self.finished = False
        self.cur_max_speed = 0.0
        self.cur_target_linear = 0.0
        self.cur_target_angular = 0.0
        
        self.linear_pos = 0.0
        self.angular_pos = 0.0
        self.decel_pos = 0.0
        self.decel_pos_ang = 0.0
        
        self.led1msg = Led()
        self.led2msg = Led()
        
    def odom_callback(self, msg):
        x = msg.pose.pose.position.x
        y = msg.pose.pose.position.y
        z = msg.pose.pose.orientation.z
        w = msg.pose.pose.orientation.w
        siny_cosp = 2 * w * z
        cosy_cosp = 1 - 2 * z * z
        yaw = math.atan2(siny_cosp, cosy_cosp)
        degree = yaw * 180 / math.pi
        #print ('x: %f y: %f Orientation: %f' % (x, y, degree))
        self.linear_pos = x
        self.angular_pos = degree
        
    def led_callback(self):
        
        if self.cur_target_angular != 0:    #angular move
            #print('bug2')
            if self.current_angular == 0:    #not turning - lights off
                self.led1msg.value = 0 #off
                self.led2msg.value = 0 #off
            elif self.current_angular > 0:  #left turn - LED 1 blink
                print('1')
                #self.led2msg.value = 0 #off
                if self.led1msg.value == 2:
                    self.led1msg.value = 0 #off
                else:
                    self.led1msg.value = 2 #orange
            else:                           #right turn - LED 2 blink
                print('help')
                #self.led1msg.value = 0 #off
                if self.led2msg.value == 2:
                    print('2')
                    self.led2msg.value = 0 #off
                else:
                    self.led2msg.value = 2 #orange
        elif self.current_linear < 0:    #backward move
            self.led1msg.value = 2 #orange
            self.led2msg.value = 2 #orange
        else:
            #print('bug')
            self.led1msg.value = 0 #off
            self.led2msg.value = 0 #off
        
        self.pubLed1.publish(self.led1msg)
        self.pubLed2.publish(self.led2msg)
        
    def move_callback(self):
        cmd = Twist()
        
        if abs(self.cur_max_speed) > 0:
            if self.cur_target_angular == 0:    #linear move
                print("LIN POS: ", self.linear_pos)
                print("SPEED: ", self.cur_max_speed)
                if (self.cur_max_speed > 0 and self.linear_pos >= self.cur_target_linear - 0.005) or (self.cur_max_speed < 0 and self.linear_pos <= self.cur_target_linear + 0.005):    #linear move finished - stop
                    self.pub_reset.publish(Empty())
                    self.cur_max_speed = 0.0
                    self.current_linear = 0.0
                    self.current_angular = 0.0
                    self.linear_pos = 0.0
                    self.angular_pos = 0.0
                    self.cur_target_linear = 0.0
                    self.cur_target_angular = 0.0
                    self.decel_pos = 0.0
                    self.decel_pos_ang = 0.0
                    
                    self.max_speed_list.pop(0)
                    self.target_linear_list.pop(0)
                    self.target_angular_list.pop(0)
                    
                    if len(self.max_speed_list) > 0:
                        self.cur_max_speed = self.max_speed_list[0]
                        self.cur_target_linear = self.target_linear_list[0]
                        self.cur_target_angular = self.target_angular_list[0]
                        
                        
                        if self.cur_max_speed < 0:
                            self.cur_target_linear *= -1
                            self.cur_target_angular *= -1
                    else:
                        #sys.exit(0)
                        self.led1msg = Led()
                        self.led2msg = Led()
                        self.led1msg.value = 0
                        self.led2msg.value = 0
                        self.pubLed1.publish(self.led1msg)
                        self.pubLed2.publish(self.led2msg)
                        
                        
                    
                    time.sleep(2)
                    return
                    
                #elif (self.cur_max_speed > 0 and self.linear_pos >= self.cur_target_linear - self.current_linear*0.5) or (self.cur_max_speed < 0 and self.linear_pos <= self.cur_target_linear - self.current_linear*0.5):  #decelerate to 0.01
                elif abs(self.linear_pos) >= abs(self.cur_target_linear)/2 and (abs(self.current_linear) < abs(self.cur_max_speed) or abs(self.linear_pos) >= abs(self.cur_target_linear) - abs(self.decel_pos)-0.05): 
                    print("deceleration working")
                    if self.cur_max_speed > 0:
                        self.cur_max_speed = 0.05
                    else:
                        self.cur_max_speed = -0.05
                        
            elif self.cur_target_linear == 0:   #angular move
                print("ANGLE: ", self.angular_pos)
                if (self.cur_max_speed > 0 and self.angular_pos >= self.cur_target_angular - 1) or (self.cur_max_speed < 0 and self.angular_pos <= self.cur_target_angular + 1):    #angular move finished - stop
                    self.pub_reset.publish(Empty())
                    self.cur_max_speed = 0.0
                    self.current_linear = 0.0
                    self.current_angular = 0.0
                    self.linear_pos = 0.0
                    self.angular_pos = 0.0
                    self.cur_target_linear = 0.0
                    self.cur_target_angular = 0.0
                    self.decel_pos = 0.0
                    self.decel_pos_ang = 0.0
                    
                    self.max_speed_list.pop(0)
                    self.target_linear_list.pop(0)
                    self.target_angular_list.pop(0)
                    
                    if len(self.max_speed_list) > 0:
                        
                        
                        self.cur_max_speed = self.max_speed_list[0]
                        self.cur_target_linear = self.target_linear_list[0]
                        self.cur_target_angular = self.target_angular_list[0]
                        
                        if self.cur_max_speed < 0:
                            self.cur_target_linear *= -1
                            self.cur_target_angular *= -1
                    else:
                        #sys.exit(0)
                        self.led1msg = Led()
                        self.led2msg = Led()
                        self.led1msg.value = 0
                        self.led2msg.value = 0
                        self.pubLed1.publish(self.led1msg)
                        self.pubLed2.publish(self.led2msg)
                    self.pub_reset.publish(Empty())
                    time.sleep(5)
                    return
                    
                elif abs(self.angular_pos) >= abs(self.cur_target_angular)/2 and (abs(self.current_angular) < abs(self.cur_max_speed) or abs(self.angular_pos) >= abs(self.cur_target_angular) - abs(self.decel_pos_ang)-25): 
                    print("deceleration working")
                    if self.cur_max_speed > 0:
                        self.cur_max_speed = 0.1
                    else:
                        self.cur_max_speed = -0.1
        
            if self.cur_target_angular == 0:    #linear move - update linear speed
                if abs(self.cur_max_speed - self.current_linear) < self.delta_linear:
                    self.current_linear = self.cur_max_speed
                else:
                    if self.cur_max_speed > self.current_linear:
                        print('+')
                        if self.cur_max_speed > 0:
                            self.decel_pos = self.linear_pos
                            print("Decel pos: ", self.decel_pos)
                        self.current_linear += self.delta_linear
                    elif self.cur_max_speed < self.current_linear:
                        print('-')
                        if self.cur_max_speed < 0:
                            self.decel_pos = self.linear_pos
                            print("Decel pos: ", self.decel_pos)
                        self.current_linear -= self.delta_linear
                
            elif self.cur_target_linear == 0:    #angular move - update angular speed
                if abs(self.cur_max_speed - self.current_angular) < self.delta_angular:
                    self.current_angular = self.cur_max_speed
                else:
                    if self.cur_max_speed > self.current_angular:
                        if self.cur_max_speed > 0:
                            self.decel_pos = self.angular_pos
                            print("Decel pos: ", self.decel_pos_ang)
                        self.current_angular += self.delta_angular
                    elif self.cur_max_speed < self.current_angular:
                        if self.cur_max_speed < 0:
                            self.decel_pos = self.angular_pos
                            print("Decel pos: ", self.decel_pos_ang)
                        self.current_angular -= self.delta_angular
                
            cmd.linear.x = self.current_linear
            cmd.angular.z = self.current_angular
            self.pub_vel.publish(cmd)
        
                 
        
    
def main(args=None):
    rclpy.init(args=args)
    aNode = Odom()
    
    try:      
        aNode.pub_reset.publish(Empty())
        max_speed = 0.0
        target_linear = 0.0
        target_angular = 0.0
        while not aNode.finished:
            print(aNode.finished)
            move = input("Enter a move (0.0 to finish): ")
            if move == "0.0":       #finished entering all moves
                aNode.finished = True
                max_speed = 0.0
                target_linear = 0.0
                target_angular = 0.0
            else:
                move_list = [float(x) for x in move.split()]
                max_speed = move_list[0]
                if abs(move_list[1]) > 1:   #angular move
                    target_linear = 0.0
                    target_angular = move_list[1]
                else:                       #linear move
                    target_linear = move_list[1]
                    target_angular = 0.0
                    
                    
                    
                aNode.max_speed_list.append(max_speed)
                aNode.target_linear_list.append(target_linear)
                aNode.target_angular_list.append(target_angular)
                print(aNode.max_speed_list)
                print(aNode.target_linear_list)
                print(aNode.target_angular_list)
                
        while len(aNode.max_speed_list) > 0:
            aNode.cur_max_speed = aNode.max_speed_list[0]
            aNode.cur_target_linear = aNode.target_linear_list[0]
            aNode.cur_target_angular = aNode.target_angular_list[0]
            
            #stuff to make sure backwards movements and right turns are done correctly
            if aNode.cur_max_speed < 0:
                aNode.cur_target_linear *= -1
                aNode.cur_target_angular *= -1
                
            #turn off LEDs
            aNode.led1msg = Led()
            aNode.led2msg = Led()
            aNode.led1msg.value = 0
            aNode.led2msg.value = 0
            aNode.pubLed1.publish(aNode.led1msg)
            aNode.pubLed2.publish(aNode.led2msg)
            rclpy.spin(aNode)
            
        
                
            
        
    except KeyboardInterrupt:
        pass
    finally:
        aNode.destroy_node()
    if rclpy.ok():
        rclpy.shutdown()
        
if __name__ == '__main__':
    main()
