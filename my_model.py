
import torch.nn as nn

class MyModelClass(nn.Module):
	def __init__(self, input_size=2391):  # Fixed input size
		super(MyModelClass, self).__init__()
		self.model = nn.Sequential(
			nn.Linear(input_size, 512),
			nn.ReLU(),
			nn.Linear(512, 256),
			nn.ReLU(),
			nn.Linear(256, 1)  # Outputs a value score for the (state + action)
		)

	def forward(self, x):
		return self.model(x)
