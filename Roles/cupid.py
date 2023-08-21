from Roles.role import Role

'''
Class Cupid that gives information about the role "Cupid", it inherits from the class "Cupid".
It has an attribute "arrowsSent" to give if he used his arrows at the start of the game 
(used to deny him from choosing lovers more than once).
'''
class Cupid(Role):
	def __init__(self, name):
		super().__init__(name)
		self.arrowsSent = False
		self.strRole="Cupid"