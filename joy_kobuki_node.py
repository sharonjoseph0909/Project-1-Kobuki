import rclpy
from rclpy.node import Node

from sensor_msgs.msg import Joy
from geometry_msgs.msg import Twist
from std_msgs.msg import String
from kobuki_ros_interfaces.msg import Led
from kobuki_ros_interfaces.msg import Sound
from kobuki_ros_interfaces.msg import BumperEvent

class JoyKobukiNode(Node): 
    def __init__(self):
        super().__init__('joy_demo')

        self.subscription = self.create_subscription(
            Joy,
            'joy',
            self.joystick_callback,
            10)
        self.subscription
        
        self.subscription = self.create_subscription(BumperEvent, '/events/bumper',
self.bumper_callback, 10)
        self.subscription
        
        self.pub = self.create_publisher(Twist, '/cmd_vel', 10)
        self.pubLed1 = self.create_publisher(Led, '/mobile_base/commands/led1', 1)
        self.pubLed2 = self.create_publisher(Led, '/mobile_base/commands/led2', 1)
        
        self.timer = self.create_timer(2, self.timer_callback)


        self.timer = self.create_timer(0.5, self.timer_callback)
        
        self.current_linear = 0.0
        self.current_angular = 0.0
        self.target_linear = 0.0
        self.target_linear_rev = 0.0
        self.target_angular = 0.0
        self.delta_linear = 0.1
        self.delta_angular = 0.2
        self.delta_break = 0.25
        self.target_break = 0.0
        self.target_emergency_break = 0.0

        # statements for led demo
        self.backward = False
        self.brake = False
        self.forward = False
        self.left = False
        self.right = False
        self.emergencybrake = False
        self.smoother_enabled = False
        self.bumper = False
        
    def joystick_callback(self, msg):
        self.target_linear = float(1-msg.axes[5])/2 * 0.8
        self.target_linear_rev = -1.0 * (float(1-msg.axes[2])/2) * 0.8
        self.target_angular = float(msg.axes[0])
        self.target_break = float(msg.buttons[0])
        self.target_emergency_break = float(msg.buttons[1])
        
        self.brake = bool(msg.buttons[0]) # regular brake button push 
        self.emergencybrake = bool(msg.buttons[1]) # emergency brake button push 

        if msg.buttons[2] == 1: 
            self.smoother_enabled = not self.smoother_enabled
            
    def bumper_callback(self, msg):
        if msg.bumper == 0:
            print ('Left bumper: ', end="")
        elif msg.bumper == 1:
            print ('Center bumper: ', end="")
        else:
            print ('Right bumper: ', end="")
        if msg.state == 0:
            print ('Released')
            self.bumper = False
        else:
            print ('Pressed')
            self.bumper = True

    def timer_callback(self):
        cmd = Twist()
        
        #self.get_logger().debug('This is a debug message.')
        
        #emergency break
        if self.target_emergency_break == 1:
            self.current_linear = 0.0
        #break (if break pressed, slow down faster)
        elif self.target_break == 1 and not self.bumper:
            if abs(self.current_linear) < self.delta_break:
                    self.current_linear = 0.0
            else:
                if self.current_linear < 0:
                    self.current_linear += self.delta_break
                elif self.current_linear > 0:
                    self.current_linear -= self.delta_break  
        else:
            #forward
            if self.target_linear != 0 and not self.bumper:
                if abs(self.target_linear - self.current_linear) < self.delta_linear:
                    self.current_linear = self.target_linear
                else:
                    if self.target_linear > self.current_linear:
                        self.current_linear += self.delta_linear
                    elif self.target_linear < self.current_linear:
                        self.current_linear -= self.delta_linear   
            #reverse
            else:
                if self.bumper and self.current_linear > 0:
                    self.current_linear = 0.0
                    
                if abs(self.target_linear_rev - self.current_linear) < self.delta_linear:
                    self.current_linear = self.target_linear_rev
                else:
                    if self.target_linear_rev > self.current_linear:
                        self.current_linear += self.delta_linear
                    elif self.target_linear_rev < self.current_linear:
                        self.current_linear -= self.delta_linear


        #turn
        if abs(self.target_angular - self.current_angular) < self.delta_angular:
            self.current_angular = self.target_angular
        else:
            if self.target_angular > self.current_angular:
                self.current_angular += self.delta_angular
            elif self.target_angular < self.current_angular:
                self.current_angular -= self.delta_angular
            

        cmd.linear.x = self.current_linear
        cmd.angular.z = self.current_angular
        self.pub.publish(cmd)

        self.forward = self.current_linear > 0.0
        self.backward = self.current_linear < 0.0 

        led1msg = Led()
        led2msg = Led()

        if self.emergencybrake:
            led1msg.value = 3 #off
            led2msg.value = 3       
        elif self.brake:
            led1msg.value = 0 #red
            led2msg.value = 3 #off
        elif self.backward or self.bumper:
            led1msg.value = 3 #off
            led2msg.value = 1 #orange
        else:
            if self.smoother_enabled:
                led1msg.value = 2 #green
                led2msg.value = 2 #green
            else:
                led1msg.value = 3 #off
                led2msg.value = 3 #off

        self.pubLed1.publish(led1msg)
        self.pubLed2.publish(led2msg)

def main(args=None):
    rclpy.init(args=args)
    aJoy = JoyKobukiNode()
    try:
        rclpy.spin(aJoy)
        
    except KeyboardInterrupt:
        pass
    finally:
        aJoy.destroy_node()
        if rclpy.ok():
            rclpy.shutdown()
        
if __name__== '__main__':
    main()
