import cupy as cp

print("GPU:", cp.cuda.runtime.getDeviceProperties(0)["name"])

# GPU memory allocation and transfer
a = cp.asarray([1, 2, 3], dtype=cp.float32)
print("Transfer:", cp.asnumpy(a))

# Elementwise CUDA kernel
b = a * 2
print("Elementwise:", cp.asnumpy(b))

# Reduction
print("Sum:", cp.sum(a).item())

# cuBLAS
m = cp.eye(4, dtype=cp.float32)
print("Matrix multiplication:", cp.asnumpy(m @ m))