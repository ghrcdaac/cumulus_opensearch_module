import os
import shutil
import subprocess
import sys


lambda_dir = f'{os.path.dirname(os.path.realpath(__file__))}'
task_dir = f'{lambda_dir}/task'
temp_dir = f'{lambda_dir}/temp'

print(f'Installing package requirements...')
# Install requirements
os.makedirs(temp_dir, exist_ok=True)
subprocess.check_call([sys.executable, '-m', 'pip', 'install',
                       '-r', f'{task_dir}/requirements.txt', '--target', temp_dir,
                       '--force-reinstall'], stdout=sys.__stdout__)
print('Installation complete...')

print('Copying source files...')
# Copy source files
dest_dir = f'{temp_dir}/task/'
os.makedirs(dest_dir, exist_ok=True)
for ele in os.listdir(task_dir):
    print(ele)
    if ele.endswith('.py'):
        src_file = f'{task_dir}/{ele}'

        print(f'copying [src, dest]: [{src_file}, {dest_dir}]')
        result = shutil.copy(src_file, dest_dir)
        print(result)
print('Copying complete...')

print('Creating lambda zip archive...')
# Make archive and cleanup temp directory
shutil.make_archive(f'{lambda_dir}/opensearch_package', 'zip', temp_dir)
print('Archive creation complete...')

print('Cleaning up temp directory...')
shutil.rmtree(temp_dir)
print('Complete')
