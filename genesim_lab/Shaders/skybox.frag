#version 330 core

out vec4 fragColor;

in vec4 clipCoords;

uniform samplerCube u_texture_cubemap_skybox;
uniform mat4 m_invProjView;
uniform vec3 SunPos;
uniform vec3 MoonPos;

vec3 SunRadCol = vec3 (255, 255, 255) / 255;
vec3 MoonRadCol = vec3 (255, 255, 118) / 255;
vec3 NightCol = vec3 (0, 0, 30) / 255;
vec3 TwilightCol = vec3 (255, 153, 153) / 255;


void main() {
    // Computes Cube map coordinates
    vec4 worldCoords = m_invProjView * clipCoords;
    vec3 texCubeCoord = normalize(worldCoords.xyz / worldCoords.w);

    // Fragment vicinity to Sun and Moon bodies [averaged over max distante in a 2x2x2 cube]
    float SunProximity = (2.0*sqrt(3.0) - length(texCubeCoord - SunPos))/(2.0*sqrt(3.0));
    float MoonProximity = (0.15 - length(texCubeCoord - MoonPos))/(2.0*sqrt(3.0));

    // Fragment vicinity to Sun over y axis and XZ plane alone
    float SunHorizonY = (2.0 - abs(texCubeCoord.y - SunPos.y)) / 2.0;
    float SunHorizonXZ = (2.0 - abs(length(texCubeCoord.xz - SunPos.xz))) / 2.0;

    // Weights for body radiation, twilight and night
    float SunVisibility = min(1.0, pow(1.0 + SunPos.y, 2.0)); // Over or below XZ plane

    float SunWeight = pow(SunProximity, 2.5) * 0.6;
    float NightWeight = pow(1.0 - SunProximity, 0.2) * 1.0 * abs((-1.0 + SunPos.y))/2.0;
    float MoonWeight = MoonProximity * 0.3;

    float TwilightWeightY = pow(SunHorizonY, 3.0) * 0.7;
    float TwilightWeightXZ = pow(SunHorizonXZ, 0.5) * 0.8;

    // Basic texture extraction and color differential maps for Twilight and Night
    fragColor = texture(u_texture_cubemap_skybox, texCubeCoord);
    vec3 TwilightFragDiff = fragColor.rgb - TwilightCol;
    vec3 NightFragDiff = fragColor.rgb - NightCol;

    // Fragment modification
    // Day and Night cycle
    fragColor.rgb = fragColor.rgb * (1 - SunWeight) + SunRadCol * SunWeight * SunVisibility - NightFragDiff * NightWeight;
    // Twilight
    fragColor.rgb -= TwilightFragDiff * TwilightWeightY * (1 - abs(texCubeCoord.y)) * TwilightWeightXZ * (1.0 - abs(SunPos.y));
    // Moon radiation
    fragColor.rgb = fragColor.rgb * (1 - MoonWeight) + MoonRadCol * MoonWeight;
}