import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from tkinter import Frame


class Graphics(Frame):
    def __init__(self, parent):
        super().__init__(parent)

        self.canvas = None
        self.my_figure = None
        self.parent = parent

        self.init_ui()

    def init_ui(self):
        self.my_figure = plt.Figure(figsize=(1, 1), dpi=100, linewidth=0.5, edgecolor='gray')
        self.my_figure.subplots_adjust(left=0.1, bottom=0.1, right=0.9, top=0.95, wspace=0, hspace=0.4)

        self.canvas = FigureCanvasTkAgg(self.my_figure, master=self.parent)
        self.canvas.draw()
        self.canvas.get_tk_widget().pack(fill="both", expand=1, padx=10, pady=10)

    def set_axis(self, n_graphs, graphs_title, x_label, y_labels):
        ax = []
        for i in range(n_graphs):
            ax.append(self.my_figure.add_subplot(int(str(n_graphs) + '1' + str(i + 1))))
            ax[i].xaxis.label.set_color('black')
            ax[i].yaxis.label.set_color('black')
            ax[i].set(ylabel=y_labels[i])
            ax[i].ticklabel_format(axis="y", style="sci", scilimits=(0, 0))

        ax[0].set(title=graphs_title)
        ax[-1].set(xlabel=x_label)

        return ax


