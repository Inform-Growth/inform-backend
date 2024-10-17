import platform
import subprocess


def install_requirements():
	"""
	Method used to properly set up your python environment based on your platform:
		- macOS/Linux
		- Windows
	"""
	# Detect current OS
	current_os = platform.system()
	
	if current_os == 'Windows':
		requirements_file = 'windows_requirements.txt'
	else:
		requirements_file = 'linux_requirements.txt'
		
	# Install packages via pip
	subprocess.check_call(['pip', 'install', '-r', requirements_file])
	
	
if __name__ == '__main__':
	install_requirements()