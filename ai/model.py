
import torch.nn as nn

class Model(nn.Module):
	def __init__(self, input_size=2391):  # Fixed input size
		super(Model, self).__init__()  # <-- This is the correct super call
		self.model = nn.Sequential(
			nn.Linear(input_size, 512),
			nn.ReLU(),
			nn.Linear(512, 256),
			nn.ReLU(),
			nn.Linear(256, 1)  # Outputting a value for state+action
		)

	def forward(self, x):
		return self.model(x)
