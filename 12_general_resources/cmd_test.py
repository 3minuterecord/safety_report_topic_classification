import sys

def main():
        calc = (int(sys.argv[1]) + int(sys.argv[2]))
        print(f'Hello my test calc, answer = {calc}')
        return(calc)      
        
if __name__ == "__main__":
        main()