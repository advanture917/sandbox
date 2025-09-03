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
import time
code = """
import numpy as np
import matplotlib.pyplot as plt

def simple_charts():
    # 生成示例数据
    x = np.arange(1, 11)
    y1 = np.random.randint(1, 10, 10)
    y2 = np.random.randint(1, 10, 10)
    
    # 创建图表
    plt.figure(figsize=(12, 4))
    
    # 折线图
    plt.subplot(131)
    plt.plot(x, y1)
    plt.title('Line Chart')
    plt.grid(True)
    
    # 柱状图
    plt.subplot(132)
    plt.bar(x, y2)
    plt.title('Bar Chart')
    
    # 散点图
    plt.subplot(133)
    plt.scatter(x, y1, color='red')
    plt.title('Scatter Plot')
    
    # 调整布局并显示
    plt.tight_layout()
    save_path = f"output/xxx.svg"
    plt.savefig(save_path,format='svg', dpi=300, bbox_inches='tight')
    plt.close()  # 关闭当前图形，释放内存
    print(f"已保存: {save_path}")

if __name__ == "__main__":
    simple_charts()

"""

libraries = ['numpy','matplotlib']
with SandboxSession() as sb:
    result = sb.run_code(code =code ,dependencies= libraries )
    time.sleep(30)
    print("stdout:", result)