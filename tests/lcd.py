import sys
sys.path.insert(0,'../')

import devices.displays.hd44780 as hd44780

lcd = hd44780.HD44780(0x27, 0, numlines=4)

lcd.printline(0,'SensorsPy Test')
