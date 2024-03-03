in vec4 colour;
in float offset;

void main(void)
{
    gl_FragColor = colour;
    gl_FragDepth = gl_FragCoord.z + offset;
}
