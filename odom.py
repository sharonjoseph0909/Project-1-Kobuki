import rclpy
from rclpy.node import Node
from nav_msgs.msg import Odometry
from kobuki_ros_interfaces.msg import BumperEvent
from geometry_msgs.msg import Twist
from std_msgs.msg import Empty

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
        
        self.timer = self.create_timer(0.1, self.move_callback)
        
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
        
    def move_callback(self):
        cmd = Twist()
        
        if self.cur_max_speed > 0:
            print(self.linear_pos)
            if self.linear_pos == self.cur_target_linear:    #linear move finished - stop
                self.cur_max_speed = 0.0
                self.current_linear = 0.0
                self.max_speed_list.pop(0)
                self.target_linear_list.pop(0)
                self.target_angular_list.pop(0)
                self.pub_reset.publish(Empty())
            elif self.linear_pos > self.cur_target_linear - 0.25:  #decelerate to 0.01
                cur_max_speed = 0.01
        
            if self.cur_target_angular == 0:    #linear move
                if abs(self.cur_max_speed - self.current_linear) < self.delta_linear:
                    self.current_linear = self.cur_max_speed
                else:
                    if self.cur_max_speed > self.current_linear:
                        self.current_linear += self.delta_linear
                    elif self.cur_max_speed < self.current_linear:
                        self.current_linear -= self.delta_linear
                
            elif self.cur_target_linear == 0:    #angular move
                move = 0
                
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
                
                rclpy.spin(aNode)
                
            
        
    except KeyboardInterrupt:
        pass
    finally:
        aNode.destroy_node()
    if rclpy.ok():
        rclpy.shutdown()
        
if __name__ == '__main__':
    main()
