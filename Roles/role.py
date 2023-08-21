'''
Class Role that gives common information about anyone in the game that has any kind of role.
It has multiple attributes :
-"name" to identify who is who
-"alive" to give if the player is alive or dead
-"inLove" to give if the player is in love with another player or not
-"vote" to give who the player voted during the day.
'''
class Role:
	def __init__(self, name):
		self.name = name
		self.alive = True
		self.inLove = ""
		self.vote = ""



