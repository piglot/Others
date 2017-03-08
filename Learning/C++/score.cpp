#include <iostream>
#include <assert.h>
using namespace std;

int cal_score(int score[], int judge_type[], int n)  
{
	assert(n>0);
	int specialistScore = 0;
	int specialistNum = 0;
	int popularScore = 0;
	int popularNum = 0;
	for (int i=0; i<n; ++i) {
		if (judge_type[i]==1) {
			++specialistNum;
			specialistScore += score[i];
		} else if (judge_type[i]==2) {
			++popularNum;
			popularScore += score[i];
		}
	}
	if (specialistNum && popularNum) {
		return int(int(double(specialistScore)/specialistNum+0.5)*0.6+int(double(popularScore)/popularNum+0.5)*0.4+0.5);
	} else if (specialistNum && !popularNum)
		return int(double(specialistScore)/specialistNum+0.5);
	else
		return 0;//无专家的情况
}


int main(int argc, char **argv)
{
	int score[10]={1,2,3,5,6,7,8,9,4,7};
	int judge_type[10]={1,1,1,1,1,1,1,1,1,1};
	int n=10;
	int avar=cal_score(score,judge_type,10);
	cout<<avar<<endl;

	return 0;
}

