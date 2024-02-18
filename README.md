As a prerequisite, you will need Avahi/Bonjour installed (due to zeroconf package). On a Raspberry Pi, you can get it with:

```bash
sudo apt-get update    
sudo apt-get install pigpio python-pigpio python3-pigpio
sudo apt-get install libavahi-compat-libdnssd-dev

```


Before starting run the pigpiod
```bash
sudo pigpiod
```

If you get a 'no handle available' run
```bash
sudo killall pigpiod
```


for installing pyaudio
```bash
sudo apt-get install libportaudio0 libportaudio2 libportaudiocpp0 portaudio19-dev
```