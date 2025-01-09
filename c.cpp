#include <iostream>
#include <vector>
#include <string>
#include <cctype>
using namespace std;

void splChar(const string& s)
{
    int count = 0;
    for (char a : s) {
        if (((a < 65) || (a > 122) || (a > 90 && a < 97))&& a!=' ') {
            count++;
        }
    }
    cout << "Spl char: " << count << endl;
}

string toCaps(const string& s) {
    string result = s;
    for (char& c : result) 
    {
        c = toupper(c);
    }
    return result;
}

void vowels(const string& s) {
    int vowelCount = 0;
    for (char a : s) {
        if (a == 'a' || a == 'e' || a == 'i' || a == 'o' || a == 'u' || 
            a == 'A' || a == 'E' || a == 'I' || a == 'O' || a == 'U') {  
            cout << a<<endl;
            vowelCount++;
        }       
    }
    cout << "cnt: " << vowelCount << endl;
}

void whiteSpace(const string& s) {
    int spaces = 0;
    int tabs = 0;
    int newlines = 0;
    int conse = 0;

    for (char a : s) {
        if (a == ' ') {
            conse++;
            if (conse == 4) {
                tabs++;
                conse = 0;
            } else {
                spaces++;
            }
        } else {
            conse = 0; 
            if (a == '\t') {
                tabs++;
            }
        }
    }
    spaces += conse;

    cout << "Spaces: " << spaces << endl;
    cout << "Tabs: " << tabs << endl;
}
int main() 
{
    vector<string> sstr;
    string str;
    cout << "begin"<<endl;
    while (true) 
    {
        getline(cin, str); 
        if (str.empty()) 
        { 
            break;
        }
        sstr.push_back(str);
    }

    int newl=1;
    for (const auto& i : sstr) {
        string res = toCaps(i);
        cout << res << endl;
        vowels(i);
        whiteSpace(i);
        newl++;
        cout << "Newlines: " << newl << endl;
        splChar(i);
    }

    return 0;
}