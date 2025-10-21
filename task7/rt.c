int mul_using_add(int x, int y) {
    unsigned mask = 1;
    int i = 0;
    int res = 0;
    while (mask != 0) {
        if (mask & x) {
            res += y << i;
        }
        mask <<= 1;
        i++;
    }
    return res;
}