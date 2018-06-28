#!/usr/bin/env python

import qi, threading, rospy

from time import sleep

from robotendpoint_aura.msg import RoboBookmark, RoboSpeech


loglevel = rospy.get_param('/debug/loglevel', rospy.INFO)

rospy.init_node('robotendpoint', anonymous=False, log_level=loglevel)
pepperip = rospy.get_param(rospy.get_namespace() + 'pepperip', "192.168.100.52")

class PepperDriver:
    """description of class"""
    def __init__(self, ipaddress):
        self._running = True
        self._app = None
        self._mem = None
        self._tts = None
        self._subbookmark = None
        self._behav = None
        self._bookmarkcb = None
        self._ipaddress = "tcp://" + ipaddress + ":9559"
        self._appthread = None
        self._setup()

    def say(self, speech):
        rospy.loginfo("robot say: {}".format(speech.text))
        self._tts.say(speech.text, _async=False)

    def setBookmarkCallback(self, callback):
        if callback is not None:
            self._bookmarkcb = callback
            self._subbookmark = self._mem.subscriber("ALTextToSpeech/CurrentBookMark")
            self._subbookmark.signal.connect(callback)

    def launch(self, app):
        self._behav.startBehavior(app)

    def stop(self):
        rospy.loginfo("Calling naoqi app stop.")
        self._app.stop()
        if self._appthread:
            self._appthread.join()

    def _setup(self):
        self._running = True
        self._app = qi.Application(url=self._ipaddress)
        self._app.start()
        self._appthread = threading.Thread(target=self._appspin).start()
        self._mem = self._app.session.service("ALMemory")
        self._tts = self._app.session.service("ALAnimatedSpeech")
        self._behav = self._app.session.service("ALBehaviorManager")

    def _appspin(self):
        if self._running:
            try:
                self._app.run()
                self._running = False
                rospy.loginfo("Naoqi App closing gracefully.")
            except:
                rospy.logerror("Unexpected error in naoqi, attempting restart in 5 seconds: {}".format(sys.exc_info()[0]))
                sleep(5.0)
                self._setup()

pepper = PepperDriver(pepperip)

robobmpub = rospy.Publisher(rospy.get_namespace() + 'robobookmark', RoboBookmark, queue_size=10)

def bookmarkcb(bookmark):
    if bookmark != 0:
        rospy.loginfo("Publishing bookmark {}".format(bookmark))
        robobm = RoboBookmark()
        robobm.bookmark = bookmark
        robobmpub.publish(robobm)

pepper.setBookmarkCallback(bookmarkcb)

rospy.Subscriber(rospy.get_namespace() + 'robospeech', RoboSpeech, pepper.say)

while not rospy.is_shutdown():
    try:
        rospy.spin()
    except:
        pass

#pepper.stop()

rospy.loginfo("robotendpoint node shutdown")
