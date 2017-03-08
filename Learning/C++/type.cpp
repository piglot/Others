#include<iostream>
#include<stdio.h>

using namespace std;

int main()
{
	float a=0.0f;
	cout<<(int&)a<<endl;
	cout<<(int)a<<endl;
	cout<<dec<<a<<endl;
	cout<<hex<<a<<endl;
	cout<<&a<<endl;
	cout<<boolalpha<<((int)a==(int &)a)<<endl;

	return 0;
}


