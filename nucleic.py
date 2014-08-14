###
#AUTHOR: Nathaniel Watson
###

def dnaRevComp(x):
	"""
	Function : Returns the reverse complement of a string consisting of the letters A,C,G,T,N.
	Args     : x - str.
	Returns  : str.
        Example: Given that x is ACCTG, returns CAGGT
	"""
	from string import maketrans
	x = x[::-1]
	start="ACGTN"
	end = "TGCAN"
	transtab = maketrans(start,end)
	return x.translate(transtab)

