import argparse  


def main():  
    # 创建解析器  
    parser = argparse.ArgumentParser(description='Parse command line arguments and print them.')  
    
    # 添加参数  
    parser.add_argument('--action', type=str, help='The parameter to be printed', required=True)  
    
    # 解析参数  
    args = parser.parse_args()  
    
    # 打印参数  
    print(f'Successfully executed : {args.action}')  

if __name__ == '__main__':  
    main()  
