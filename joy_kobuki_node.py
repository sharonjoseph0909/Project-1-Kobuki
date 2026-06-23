import rclpy
from rclpy.node import Node

from sensor_msgs.msg import Joy
from geometry_msgs.msg import Twist
from std_msgs.msg import String

class JoyKobukiNode(Node): 
    def __init__(self):
        super().__init__('joy_demo')
        self.subscription = self.create_subscription(
            Joy,
            'joy',
            self.joystick_callback,
            10)
        self.subscription
        
        self.pub = self.create_publisher(Twist, '/cmd_vel', 10)
        
        self.timer = self.create_timer(0.5, self.timer_callback)
        
        self.current_linear = 0.0
        self.current_angular = 0.0
        self.target_linear = 0.0
        self.target_linear_rev = 0.0
        self.target_angular = 0.0
        self.delta_linear = 0.1
        self.delta_angular = 0.2
        self.delta_break = 0.25
        
    def joystick_callback(self, msg):
        self.target_linear = float(1-msg.axes[5])/2
        self.target_linear_rev = -1.0 * (float(1-msg.axes[2])/2)
        self.target_angular = float(msg.axes[0])
        
        
    def timer_callback(self):
        cmd = Twist()
        
        #forward
        if abs(self.target_linear - self.current_linear) < self.delta_linear:
            self.current_linear = self.target_linear
        else:
            if self.target_linear > self.current_linear:
                self.current_linear += self.delta_linear
            elif self.target_linear < self.current_linear:
                self.current_linear -= self.delta_linear
               
        #reverse
        if self.target_linear == 0:
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
