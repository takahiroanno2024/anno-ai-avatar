using UnityEngine;
using UnityEditor;

public class TextureImporterSettings : AssetPostprocessor
{
    void OnPreprocessTexture()
    {
        TextureImporter textureImporter = (TextureImporter)assetImporter;

        // "Slides/sample_PDF/"フォルダ内の画像に対してのみ適用
        if (assetPath.StartsWith("Assets/Resources/Slides/manifest_demo_PDF"))
        {
            textureImporter.textureType = TextureImporterType.Sprite;
        }
    }

    [MenuItem("Assets/Set Texture Type to Sprite")]
    public static void SetTextureTypeToSprite()
    {
        string folderPath = "Assets/Resources/Slides/manifest_demo_PDF";
        string[] guids = AssetDatabase.FindAssets("t:Texture", new[] { folderPath });

        foreach (string guid in guids)
        {
            string path = AssetDatabase.GUIDToAssetPath(guid);
            TextureImporter textureImporter = AssetImporter.GetAtPath(path) as TextureImporter;

            if (textureImporter != null)
            {
                textureImporter.textureType = TextureImporterType.Sprite;
                AssetDatabase.ImportAsset(path, ImportAssetOptions.ForceUpdate);
            }
        }

        Debug.Log("All textures in " + folderPath + " have been set to Sprite.");
    }
}