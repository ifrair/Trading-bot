import matplotlib.pyplot as plt

def draw_dataset(table):
    plt.rcParams["figure.figsize"] = (300,4.5)
    table.plot(x='Middle time', y=['Middle', 'Low', 'High'])
    ax = table.plot(x='Middle time', y=['CCI'])
    ax.axhline(y=100, xmin=-1, xmax=1, color='r', linestyle='--', lw=1)
    ax.axhline(y=0, xmin=-1, xmax=1, color='g', linestyle='--', lw=1)
    ax.axhline(y=-100, xmin=-1, xmax=1, color='r', linestyle='--', lw=1)
    plt.show()
