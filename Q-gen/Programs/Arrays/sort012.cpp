#include <iostream>
using namespace std;

void swapChar(char* a, char* b)
{
    char temp = *a;
    *a = *b;
    *b = temp;
}

string sort012(string s, int n)
{
    int lo = 0;
    int hi = n-1;
    int mid = 0;

    while (mid <= hi) 
    {
        if (s[mid] == '0') swapChar(&s[lo++], &s[mid++]);
        else if (s[mid] == '1') mid++;
        else swapChar(&s[mid], &s[hi--]);
    }

    return s;
}

int main()
{
    string s;
    cout << "Input: ";
    cin >> s;
    cout << "Output: " << sort012(s, s.size());
    return 0;
}