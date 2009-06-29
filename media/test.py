q = 0
n = 10
for i in range(n):
	for j in range(i+1, n):
		print i, j, q, "(", i * (i - 1) / 2 + j, ")"
		q += 1
