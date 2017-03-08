#include<iostream>
using namespace std;

#define P(A) cout<<#A<<": "<<(A)<<endl;
#define BUFSIZE 1024
#define AFTERX(x) X_ ##x
#define XAFTER(x) AFTERX(x)

int main(){
	int a=1, b=2, c=3;
	P(a);
	P(b);
	P(c);
	P(a+b);
	P((c-a)/b);
	P(BUFSIZE);
	P(XAFTER(BUFSIZE));
	return 0;
}
