from multipart import file_path
from sandbox.session import  SandboxSession
from sandbox.const import BackendType
code ="""
import numpy as np

# Create an array
arr = np.array([1, 2, 3, 4, 5])
print(f"Array: {arr}")
print(f"Mean: {np.mean(arr)}")
print(f"Sum: {np.sum(arr)}")
"""
libraries = ['numpy']
with SandboxSession(backend_type= BackendType.DOCKER) as sb:
    result = sb.run_code(code =code ,dependencies= libraries)
    # 这里得到的 result为
    # CommandResult(exit_code=0, stdout='Array: [1 2 3 4 5]\nMean: 3.0\nSum: 15\n', stderr='')

    print("stdout:", result)



code = """
with open('test12.txt', 'w') as file:
    file.write('hello')
"""

file_path = ['test12.txt']
with SandboxSession(backend_type= BackendType.DOCKER) as sb:
    result = sb.run_code(code =code,file_path=file_path)
    # 这里result 为本地文件的路径
    #  ['./output\\test12.txt']
    print("stdout:", result)
