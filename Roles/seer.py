from Roles.role import Role

'''
Class Seer that is used to give information about the role "Seer", it inherits from the class "Role".
It has one particular attribute "personGuessed" to give who the seer asked to predict the role during the round.
'''
class Seer(Role):
	def __init__(self, name):
		super().__init__(name)
		self.personGuessed = ""
		self.strRole="Seer"

