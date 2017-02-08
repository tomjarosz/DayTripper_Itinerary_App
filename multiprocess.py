from multiprocessing import Pool
from time import strftime
import time

def f(x):
    print('working on value {}'.format(x))
    time.sleep(x)
    # complicated processing
    return x+1

def main():
    print('Process started at: {pdate}'.format(pdate=strftime("%Y-%m-%d %H:%M:%S", )))

    # x is a list with the different values we want to iterate over    
    x = range(10)

    # here we say "run f(x) in parallel processes, taking the list of values in x"
    with Pool(processes=5) as pool:
        y_parallel = pool.map(f, x)

    print(y_parallel)

    # Notice that it would take about 45 seconds to run this whole file; 
    # but running in parallel it takes about 13 seconds.
    print('Process finished at: {pdate}'.format(pdate=strftime("%Y-%m-%d %H:%M:%S", )))

if __name__ == '__main__':
    main()