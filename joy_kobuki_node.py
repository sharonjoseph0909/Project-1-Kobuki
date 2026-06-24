import rclpy
from rclpy.node import Node

from sensor_msgs.msg import Joy
from geometry_msgs.msg import Twist
from std_msgs.msg import String
from kobuki_ros_interfaces.msg import Led
from kobuki_ros_interfaces.msg import Sound

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
        self.pubLed1 = self.create_publisher(Led, '/commands/led1', 1)
        self.pubLed2 = self.create_publisher(Led, '/commands/led2', 1)
        
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

        # statements for led demo
        self.backward = False
        self.brake = False
        self.forward = False
        self.left = False
        self.right = False
        self.emergencybrake = False
        self.smoother = False
        self.bumper = False
        
    def joystick_callback(self, msg):
        self.target_linear = float(1-msg.axes[5])/2 * 0.8
        self.target_linear_rev = -1.0 * (float(1-msg.axes[2])/2) * 0.8
        self.target_angular = float(msg.axes[0])
        
        self.brake = bool(msg.buttons[0]) # regular brake button push 
        self.emergencybrake = bool(msg.buttons[1]) # emergency brake button push 

        if msg.buttons[2] == 1: 
            self.smoother_enabled = not self.smoother_enabled

    def timer_callback(self):
        cmd = Twist()
        
        #forward
        if self.target_linear != 0:
            if abs(self.target_linear - self.current_linear) < self.delta_linear:
                self.current_linear = self.target_linear
            else:
                if self.target_linear > self.current_linear:
                    self.current_linear += self.delta_linear
                elif self.target_linear < self.current_linear:
                    self.current_linear -= self.delta_linear   
        #reverse
        else:
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
            
        #brake (led turns red)
        if self.emergencybrake:
            self.current_linear = 0.0
            self.current_angular = 0.0
        
        elif self.bumper:
            self.current_angular = 0.0

            if self.target_linear_rev < 0:
                self.current_linear = self.target_linear_rev
            else:
                self.current_linear = 0.0

        elif self.brake:
            if self.current_linear > 0:
                self.current_linear = max(0.0, self.current_linear - self.delta_break)
            elif self.current_linear < 0:
                self.current_linear = min(0.0, self.current_linear + self.delta_break)

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

class LedDemo(Node):
    def __init__(self):
        super().__init__('sound_demo')
        self.names = ['RED', 'ORANGE', 'GREEN', 'OFF']
        self.counter = 3
        self.ledNumber = 1

    def timer_callback(self):

        if self.isenable == True:
            pass
        else:
            self.backward = False
            self.brake = False
            self.forward = False  
            self.left = False
            self.right = False

        if self.pubLed1.get_subscription_count() == 0:
            print ('Waiting for a subscriber of led1. ')
        if self.pubLed2.get_subscription_count() == 0:
            print ('Waiting for a subscriber of led2. ')
        msg = Led()
        msg.value = self.counter
        print ('Led%i - msg.value = %i [%s]' % (self.ledNumber, msg.value,
    self.names[msg.value]))
        
        if self.ledNumber == 1:
            self.pubLed1.publish(msg)
        else:
            self.pubLed2.publish(msg)
        self.counter = 3
        if self.ledNumber == 1:
            self.ledNumber = 2
        else:
            raise SystemExit
        
    def main(args=None):
        rclpy.init(args=args)
        aNode = LedDemo()
        try:
            rclpy.spin(aNode)
        except (KeyboardInterrupt, SystemExit):
            pass
        finally:
            aNode.destroy_node()
            if rclpy.ok():
                rclpy.shutdown()

    if __name__ == '__main__':
        main()