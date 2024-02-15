#include <iostream>
#include <chrono>
#include <thread>

int fibonacci(int n) {
    if (n <= 1) {
        return n;
    } else {
        return fibonacci(n - 1) + fibonacci(n - 2);
    }
}

void cpu_intensive_task() {
    auto start_time = std::chrono::high_resolution_clock::now();
    int result = fibonacci(30);  // 计算斐波那契数列的第30个数字
    auto end_time = std::chrono::high_resolution_clock::now();
    std::cout << "进程任务完成，用时："
              << std::chrono::duration_cast<std::chrono::milliseconds>(end_time - start_time).count()
              << " 毫秒" << std::endl;
}

int main() {
    auto start_time = std::chrono::high_resolution_clock::now();
    // 运行100个进程任务
    for (int i = 0; i < 100; ++i) {
        std::thread(cpu_intensive_task).detach();
    }

    // 等待所有线程结束
    std::this_thread::sleep_for(std::chrono::seconds(3));

    auto end_time = std::chrono::high_resolution_clock::now();
    std::cout << "主程序执行完成，总用时："
              << std::chrono::duration_cast<std::chrono::milliseconds>(end_time - start_time).count()
              << " 毫秒" << std::endl;

    return 0;
}
