"""
This is an ugly way to listen to and send whispers at twitch.tv using twisted

We needed two IRC sockets to communicate with each other, I set them up as a global
Don't do this at home, you might get screamed at by experienced programmers
It probably isn't dealing well with disconnects,, so please 

Class Bot serves for communicating with normal irc (stream channel)
Class BotWhisper is connected to group chat server and can send and receive whispers

Send whispers from stream channel through:
    global whisperfactory
    whisperfactory.protocol.whisper(user, msg)

Settings should be obvious, channel is your stream channel, USE LOWERCASE

Feel free to use and edit this code at will
"""

from twisted.words.protocols import irc
from twisted.internet import reactor, protocol

settings = dict(
    nickname =  '',
    oauth = '',
    channel = ''
)


class Bot(irc.IRCClient):

    nickname = settings['nickname']
    password = settings['oauth']
    
    def connectionMade(self):
        irc.IRCClient.connectionMade(self)

    def connectionLost(self, reason):
        irc.IRCClient.connectionLost(self, reason)

    def signedOn(self):
        print "Main signed on"
        self.join(self.factory.channel)

    def joined(self, channel):
        print "Main joined", channel
        self.msg(channel, 'hi')

    def privmsg(self, user, channel, msg):
        user = user.split('!', 1)[0]
        print channel, user, msg

    def action(self, user, channel, msg):
        user = user.split('!', 1)[0]
        print channel, user, msg


class BotWhisper(irc.IRCClient):

    nickname = settings['nickname']
    password = settings['oauth']
    
    def connectionMade(self):
        irc.IRCClient.connectionMade(self)

    def connectionLost(self, reason):
        irc.IRCClient.connectionLost(self, reason)

    def signedOn(self):
        print "Whisper bot signed on"
        self.sendLine("CAP REQ :twitch.tv/tags")
        self.sendLine("CAP REQ :twitch.tv/commands")

    def joined(self, channel):
        print "Whispers joined", channel

    def privmsg(self, user, channel, msg):
        print user, channel, msg

    def action(self, user, channel, msg):
        user = user.split('!', 1)[0]
        print user, msg

    def gotwhisp(self, user, msg):
        """
        Gets called when we receive a whisper
        """
        print user, msg

    def whisper(self, user, msg):
        """
        Use this to send whisper
        """
        msg = ".w {} {}".format(user, msg)
        self.msg("#jtv", msg)

    def irc_unknown(self, prefix, command, params):
        """
        This is to listen to twitch.tv/commands
        It doesn't use classic IRC RFC

        So far we only listen to PRIVMSG and WHISPER

        If you want to listen to notices etc, print out params
        and figure it from there :)
        """
        print params
        if "PRIVMSG" in params[0]:
            user = params[0].split('!', 1)[0]
            channel = params[0].split('#', 1)[1].split(" ", 1)[0]
            msg = params[0].split(':', 1)[1]
            self.privmsg(user, channel, msg)
        if "WHISPER" in params[0]:
            user = params[0].split('WHISPER ', 1)[1].split(" :")[0]
            msg = params[0].split(':', 1)[1]
            self.got_whisp(user, msg)


class BotFactory(protocol.ClientFactory):

    def __init__(self):
        self.channel = settings['channel']
        self.protocol = None

    def buildProtocol(self, addr):
        global f
        p = Bot()
        p.factory = self
        self.protocol = p
        return p

    def clientConnectionLost(self, connector, reason):
        print "Main connection lost:", reason
        connector.connect()

    def clientConnectionFailed(self, connector, reason):
        print "Main connection failed:", reason
        reactor.stop()


class BotWhisperFactory(protocol.ClientFactory):

    def __init__(self):
        self.protocol = None

    def buildProtocol(self, addr):
        global g
        p = BotWhisper()
        p.factory = self
        self.protocol = p
        return p

    def clientConnectionLost(self, connector, reason):
        print "Whisper connection lost:", reason
        connector.connect()

    def clientConnectionFailed(self, connector, reason):
        print "Whisper connection failed:", reason
        reactor.stop()


if __name__ == '__main__':
    global botfactory
    global whisperfactory
    botfactory = BotFactory()
    whisperfactory = BotWhisperFactory()
    reactor.connectTCP("irc.twitch.tv", 6667, botfactory)
    reactor.connectTCP("199.9.253.119", 6667, whisperfactory)
    reactor.run()
