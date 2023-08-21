from Roles.role import Role
'''
Class Hunter that gives information about the role "Hunter", it inherits from the class "Role".
It has an attribute "gunFired" to give if the hunter used his gun when he was dead or not (used to deny him from shooting more than once).
'''
class Hunter(Role):
	def __init__(self, name):
		super().__init__(name)
		self.playerShot = ""
		self.strRole = "Hunter"