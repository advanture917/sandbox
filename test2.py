from sandbox.session import  SandboxSession
# def run_code(self,code:str, dependencies: list[str] | None = None):
# code ="""
# import numpy as np
#
# # Create an array
# arr = np.array([1, 2, 3, 4, 5])
# print(f"Array: {arr}")
# print(f"Mean: {np.mean(arr)}")
# print(f"Sum: {np.sum(arr)}")
# """
code = b'total = 0\nfor i in range(1, 101):\n    total += i\nprint(total)'
code = code.decode('utf-8')
libraries = ['numpy']
with SandboxSession() as sb:
    result = sb.run_code(code =code ,dependencies= libraries )
    print("stdout:", result)