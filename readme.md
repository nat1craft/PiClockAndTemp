# Pi Temperature Clock with MQTT
This repository holds source code for a simple raspberry-pi based clock that also reads the temperature and humidity.  Everything is (optionally) sent to a MQTT broker.

<img src="./images/piclock.jpg" width=400>

# Hardware
- [Raspberry Pi Zero W](https://amzn.to/2PeQ0qs)  - The processor behind the clock comes from this workhouse. It is a big overkill for just time/temperature/mqtt, but it does a great job.

    [<img src="https://ws-na.amazon-adsystem.com/widgets/q?_encoding=UTF8&ASIN=B0748MPQT4&Format=_SL160_&ID=AsinImage&MarketPlace=US&ServiceVersion=20070822&WS=1&tag=nat1craft-20&language=en_US">](https://www.amazon.com/Vilros-Raspberry-Starter-Power-Premium/dp/B0748MPQT4?dchild=1&keywords=raspberry+pi+zero+w&qid=1619016479&sr=8-1&linkCode=li2&tag=nat1craft-20&linkId=b749a733f063627b4225d38201c11d27&language=en_US&ref_=as_li_ss_il)


- [16x2 MEGA2560 LCD Display](https://amzn.to/3arzD0Q) - This is the LCD display that is used to present the time/temperature etc.

    [<img src="https://ws-na.amazon-adsystem.com/widgets/q?_encoding=UTF8&ASIN=B0711WLVP9&Format=_SL160_&ID=AsinImage&MarketPlace=US&ServiceVersion=20070822&WS=1&tag=nat1craft-20&language=en_US">](https://www.amazon.com/gp/product/B0711WLVP9?ie=UTF8&psc=1&linkCode=li2&tag=nat1craft-20&linkId=a4321b8be7f033fa7dda9d4f28c95bf9&language=en_US&ref_=as_li_ss_il)


- [DHT22 Digital Temperature and Humidity Sensor](https://amzn.to/3eqXIq6) - This is what is used to provide the measurements.

    [<img src="https://ws-na.amazon-adsystem.com/widgets/q?_encoding=UTF8&ASIN=B07H2RP26F&Format=_SL160_&ID=AsinImage&MarketPlace=US&ServiceVersion=20070822&WS=1&tag=nat1craft-20&language=en_US">](https://www.amazon.com/gp/product/B07H2RP26F?ie=UTF8&psc=1&linkCode=li2&tag=nat1craft-20&linkId=72beb92062b04c265c86a1c56f96861c&language=en_US&ref_=as_li_ss_il)


