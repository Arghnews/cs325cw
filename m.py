#!/usr/bin/env python3

def main():
    print("Starting main")
    opt(0)
    opt(1,2)
    opt(2)

def opt(i, n=1):
    if i == 1:
        n = 3
    print("Opt",i,n)

if __name__ == "__main__":
    main()
