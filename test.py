import matplotlib
matplotlib.use('QtAgg')
import matplotlib.pyplot as plt

fig, ax = plt.subplots()
ax.text(0.5, 0.5, "If you see this, it works!", ha='center')
plt.show()
