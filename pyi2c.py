#!/usr/bin/env python
# encoding: utf-8
"""
Usage:
  pyi2c read ADDRESS [LENGTH] (-c | -s) [-Prtfv]
  pyi2c write ADDRESS (DATA | -f FILE | [-]) (-c | -sp) [-Prtv]
  pyi2c wipe ADDRESS [LENGTH] ( -c | -s) [-Prtfv]
  pyi2c sniff ( -c | -s) [-vf]

Arguments:
  ADDRESS                   Memory address to work with  [default: 0]
  LENGTH                    Number of bytes to read from chip or wipe
                              If LENGTH is not given, we'll figure it out
  DATA                      Data to write in ASCII, 0xABCD, or 0b0000
  [-]                       Write data from stdin if DATA nor FILE given

Options:
  --version                 Show program's version number and exit
  -f FILE, --file=FILE      File to write data to or read data from
  -v, --verbose             Increase verbosity level

  -c CHIP, --chip=CHIP      Specify chip to read/write.  Available:
                              ATMLH826    LENGTH=265 -s ??? -p 8 -b ???
                              AT24C02     LENGTH=265 -s ??? -p 8 -b ???
                              email justin@meeas.com to contribute...
  -s BIN, --slave=BIN       Four bit I2C slave address  [default: 0b1010]
  -p NUM, --page=NUM        Max write page size  [default 64 bytes]

  -P PORT, --port=PORT      Serial port for Aardvark or BusPirate
                              If PORT not given, we'll figure it out
  -r RATE, --rate=RATE      Rate to read/write in kbps  [default: 100]
  -t NUM, --timeout=NUM     Timeout for read/write in millisec  [default: 250]


# For SPI version
  -r RATE, --rate=RATE      Rate to read/write in kbps  [default: 400]
  -c CHIP, --chip=CHIP      Specify chip to read/write.  Available:
                              AT25256     LENGTH=32768 -p 64
                              25AA128     LENGTH=16384 -p 64
                              25LC128     LENGTH=16384 -p 64
                              AT25080     LENGTH=1024 -p 32
  -m MODE, --mode=MODE      SPI mode of operation  [default 0]
                              mode 0 : pol = 0, phase = 0
                              mode 3 : pol = 1, phase = 1
                              modes 1 and 2 are not supported

Copyright 2015 Justin Searle
Licensed under the GPL 3.0 or later, see <http://www.gnu.org/licenses/>
Partially adapted for BusPirate from Peter Huewe's i2c-test.py
"""
import sys
from pyBusPirateLite.I2C import *
import argparse


def i2c_write_data(data):
    i2c.send_start_bit()
    i2c.bulk_trans(len(data),data)
    i2c.send_stop_bit()


def i2c_read_bytes(address, numbytes, ret=False):
    data_out=[]
    i2c.send_start_bit()
    i2c.bulk_trans(len(address),address)
    while numbytes > 0:
        if not ret:
            print ord(i2c.read_byte())
        else:
            data_out.append(ord(i2c.read_byte()))
        if numbytes > 1:
            i2c.send_ack()
        numbytes-=1
    i2c.send_nack()
    i2c.send_stop_bit()
    if ret:
        return data_out

if __name__ == '__main__':
    parser = argparse.ArgumentParser(sys.argv[0])
    parser.add_argument("-o", "--output", dest="outfile", metavar="OUTFILE", type=argparse.FileType('wb'),
            required=True)
    parser.add_argument("-p", "--serial-port", dest="bp", default="/dev/ttyUSB0")
    parser.add_argument("-s", "--size", dest="size", type=int, required=True)
    parser.add_argument("-S", "--serial-speed", dest="speed", default=115200, type=int)
    parser.add_argument("-b", "--block-size", dest="bsize", default=256, type=int)

    args = parser.parse_args(sys.argv[1:])

    i2c = I2C(args.bp, args.speed)
    print "Entering binmode: ",
    if i2c.BBmode():
        print "OK."
    else:
        print "failed."
        sys.exit()

    print "Entering raw I2C mode: ",
    if i2c.enter_I2C():
        print "OK."
    else:
        print "failed."
        sys.exit()
        
    print "Configuring I2C."
    if not i2c.cfg_pins(I2CPins.POWER | I2CPins.PULLUPS):
        print "Failed to set I2C peripherals."
        sys.exit()
    if not i2c.set_speed(I2CSpeed._400KHZ):
        print "Failed to set I2C Speed."
        sys.exit()
    i2c.timeout(0.2)
    
    print "Dumping %d bytes out of the EEPROM." % args.size

    # Start dumping
    for block in range(0, args.size, args.bsize):
        # Reset the address
        i2c_write_data([0xa0 + ((block / args.bsize) << 1), 0])
        args.outfile.write("".join([chr(x) for x in i2c_read_bytes([0xa1 + ((block / args.bsize) << 1)], args.bsize, True)]))
    if args.size % 16 != 0:
        end = 16 * (args.size / args.bsize)
        args.outfile.write("".join([chr(x) for x in i2c_read_bytes([0xa1 + ((args.size / args.bsize) << 1)], args.size % args.bsize, True)]))
    args.outfile.close()

    print "Reset Bus Pirate to user terminal: "
    if i2c.resetBP():
        print "OK."
    else:
        print "failed."
        sys.exit()



