#version 330

in vec3 p;
in vec3 m;
in vec3 a;
in vec3 b;
in vec2 distance;
in int selected;
in int next_selected;

uniform vec4 unselected_colour;
uniform vec4 selected_colour;
uniform mat4 matrix;
uniform int interp;
uniform int mode;

out vec4 colour;
out float offset;

float t;
float t2;
float t3;
float d;
vec3 r;
vec3 dr;
vec3 ddr;


void calculate(int step) {
    t = step / (interp - 1.0);
    float mlen = 1.0 / length(m);
    t2 = t * t;
    t3 = t2 * t;
    r = (a * t3) + (b * t2) + (m * t) + p;
    dr = ((3 * a * t2) + (2 * b * t) + m) * mlen;
    ddr = ((6 * a * t) + (2 * b)) * mlen * mlen;
    d = distance.x + ((distance.y - distance.x) * t);
}


void main_line(void) {
    calculate(gl_VertexID);
    gl_Position = matrix * vec4(r, 1);
    float tc = mix(float(selected), float(next_selected), t);
    colour = mix(unselected_colour, selected_colour, tc);
}

void main_line_d(void) {
    calculate(gl_VertexID);
    gl_Position = matrix * vec4(d, r.z, 0, 1);
    float tc = mix(float(selected), float(next_selected), t);
    colour = mix(unselected_colour, selected_colour, tc);
}


float curve_mag() {
    return (dr.x * ddr.y) - (dr.y * ddr.x);
}


vec3 curve_vec() {
    vec3 right = normalize(cross(dr, vec3(0, 0, 1)));
    return right * (curve_mag() * 500);
}


void curvature(void) {
    calculate(gl_VertexID);
    colour = selected_colour;
    gl_Position = matrix * vec4(r + curve_vec(), 1);
}

void curvature_d(void) {
    calculate(gl_VertexID);
    colour = selected_colour;
    gl_Position = matrix * vec4(d, curve_mag(), 0, 1);
}


void curvature_comb(void) {
    calculate(gl_VertexID>>1);
    colour = selected_colour;
    if ((gl_VertexID & 1) == 0) r += curve_vec();
    gl_Position = matrix * vec4(r, 1);
}

void curvature_comb_d(void) {
    calculate(gl_VertexID>>1);
    colour = selected_colour;
    if ((gl_VertexID & 1) == 0)
        gl_Position = matrix * vec4(d, 0, 0, 1);
    else
        gl_Position = matrix * vec4(d, curve_mag(), 0, 1);
}

void height(void) {
    calculate(gl_VertexID>>1);
    colour = unselected_colour;
    vec4 wp;
    if ((gl_VertexID & 1) == 0) r.z = 0;
    gl_Position = matrix * vec4(r, 1);
}

void height_d(void) {
    calculate(gl_VertexID>>1);
    colour = unselected_colour;
    vec4 wp;
    if ((gl_VertexID & 1) == 0)
        gl_Position = matrix * vec4(d, 0, 0, 1);
    else
        gl_Position = matrix * vec4(d, r.z, 0, 1);

}


void main(void)
{
    switch (mode) {
        case 0:
            offset = 0;
            main_line();
            break;
        case 1:
            offset = 0.001;
            height();
            break;
        case 2:
            offset = 0.0005;
            curvature();
            break;
        case 3:
            offset = 0.001;
            curvature_comb();
            break;
        case 4:
            offset = 0;
            main_line_d();
            break;
        case 5:
            offset = 0.001;
            height_d();
            break;
        case 6:
            offset = 0.0005;
            curvature_d();
            break;
        case 7:
            offset = 0.001;
            curvature_comb_d();
            break;

    }
}
