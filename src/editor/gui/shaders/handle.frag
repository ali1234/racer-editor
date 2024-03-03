in vec4 colour;
in float offset = -0.01;

void main(void)
{
    vec2 pc = gl_PointCoord - 0.5;
    gl_FragColor = colour;
    gl_FragColor.a = 5 - (dot(pc, pc) * 20);
    gl_FragDepth = gl_FragCoord.z + offset;
}
