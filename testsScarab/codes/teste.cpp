
int main(){
    int a=0,b=0,c=0;
    int i=0;
    while (i<100000){
        a = a+b+c;
        b+=5;
        c+=b+c;
        i++;
    }
}