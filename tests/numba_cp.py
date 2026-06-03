import numpy as np
from numba import cuda
import os
os.environ['NUMBA_CUDA_DRIVER'] = 'nvcuda.dll'  # Windows

# Should now show versions instead of '?'
print(f"CUDA Available: {cuda.is_available()}")
print(f"Driver Version: {cuda.driver.get_version()}")
print(f"Runtime Version: {cuda.runtime.get_version()}")

# Minimal kernel test
@cuda.jit
def test_kernel(arr):
    i = cuda.grid(1)
    if i < arr.size:
        arr[i] = arr[i] * 2

# Run test
host_arr = np.array([1, 2, 3, 4], dtype=np.float32)
dev_arr = cuda.to_device(host_arr)
test_kernel[(4+255)//256, 256](dev_arr)
result = dev_arr.copy_to_host()

print(f"Original: {host_arr}")
print(f"Result: {result}")
print("✅ SUCCESS!" if np.allclose(result, host_arr * 2) else "❌ FAILED")