# Matrix-XMPP Bridge
This project creates a bridge between a Matrix room and an XMPP MUC. It is currently very early in development.

Originally forked from https://github.com/jfrederickson/matrix-xmpp-bridge it was heavily refactored and adopted for Python 3. Missing functionality was added (like be a bidirectional, users aliases in XMPP and Matrix, etc).

**WARNING**: this bridge isn't a "bot like" one, it REQUIRES that you have a possibility to add AS registration file to synapse's configuration file!
It is still possible to bridge XMPP MUC on other's homeserver room. Just join it and use Room ID from settings!

## Dependencies
- python3
- sleekxmpp
- requests
- flask
- flask-classy

... or just ``pip install -r requirements.txt`` :)

## Installation

Make sure you have Python 3 installed. I recommend [PyENV](https://github.com/yyuu/pyenv) for managing python versions and do not rely on system one. This guide will assume that you're installed Python 3 with PyENV.

After that clone this repo, go to source's root directory and execute:

```
pyenv local ${VERSION}
```

Where `${VERSION}` is a Python version you installed previously.

After setting local python's version install dependencies:

```
pip install -r requirements.txt
```

This could take some time.

## Configuration

- Add an AS and HS token to registration.yaml and reference it in your homeserver config as described [here](http://matrix.org/blog/2015/03/02/introduction-to-application-services/)
- Edit mxbridge.conf.example with user and room details for the Matrix/XMPP rooms you would like to bridge and save as mxbridge.conf in bot's source directory
- Start bridge.py

### Custom configuration file

There is a possibility to specify configuration file name while launching bridge. It is useful to run several independent instances using one code base. Just pass configuration file name after "bridge.py", like this:

```
./bridge.py my_custom_mxbridge.conf
```

### Synapse

Due to some (temporary) things, it is better to set `rc_messages_per_second` to 5, otherwise bridge could eat messages when it detects new XMPP user to map to Matrix.

## FAQ

Q: When I start the bridge it says "Application service cannot masquerade as this user.", but I didn't send anything yet. Is that critical?

A: No, it is only related to master user for bridge, which isn't sending any messages.

Q: Bridge eats forst message(s) after launching, WTF?

A: Shit happens. But when bridge started to transmit messages - it won't eat them anymore. So just spam until transmission starts. Usually it'll need about 2 messages for each side.
