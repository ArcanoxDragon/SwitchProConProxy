def mapRange(val, fromMin, fromMax, toMin, toMax):
    return (val - fromMin) / (fromMax - fromMin) * (toMax - toMin) + toMin