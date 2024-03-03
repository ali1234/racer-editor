in vec2 world_position;
in float offset = 0.002;

vec4 grid(vec2 pos) {
    vec2 derivative = fwidth(pos);
    vec2 grid = abs(fract(pos + 0.5) - 0.5) / derivative;

    float alphax = 1.0 - min(grid.x, 1.0);
    float alphay = 1.0 - min(grid.y, 1.0);
    float minimumx = min(derivative.x, 1.0);
    float minimumy = min(derivative.y, 1.0);

    vec2 axis = abs(pos) / derivative;
    float r = axis.x < 1.0 ? 1.0 : 0.4;
    float g = axis.y < 1.0 ? 1.0 : 0.4;

    vec4 color = vec4(r, g, 0.4, max(alphax, alphay));
    return color;
}

vec4 test(vec2 coord) {
    return vec4(coord.x, coord.y, 1.0, 1.0);
}

void main() {

    gl_FragColor = grid(world_position*0.01);
    if (gl_FragColor.a < 0.1) discard;
    gl_FragDepth = gl_FragCoord.z + offset;
}
