using System;
using System.Collections.Generic;
using System.IO;
using UnityEngine;

public class RandomBatteryImageProvider : MonoBehaviour
{
    public string imageFolderRelativeToProject = "data/images";
    public string manifestFileName = "sample_manifest.json";
    public bool recursive = true;

    readonly List<string> imagePaths = new List<string>();
    string lastImagePath;

    void Awake()
    {
        ReloadImages();
    }

    public void ReloadImages()
    {
        imagePaths.Clear();
        LoadFromConfiguredFolder();
        if (imagePaths.Count == 0)
        {
            LoadFromManifestFallback();
        }

        Debug.Log("[RandomImageProvider] Loaded " + imagePaths.Count + " test images.");
    }

    public string PickRandomImagePath()
    {
        if (imagePaths.Count == 0)
        {
            ReloadImages();
        }

        if (imagePaths.Count == 0)
        {
            Debug.LogError("[RandomImageProvider] No test images available.");
            return string.Empty;
        }

        int index = UnityEngine.Random.Range(0, imagePaths.Count);
        if (imagePaths.Count > 1)
        {
            int guard = 0;
            while (imagePaths[index] == lastImagePath && guard < 12)
            {
                index = UnityEngine.Random.Range(0, imagePaths.Count);
                guard++;
            }
        }

        lastImagePath = imagePaths[index];
        Debug.Log("[RandomImageProvider] Selected image: " + lastImagePath);
        return lastImagePath;
    }

    void LoadFromConfiguredFolder()
    {
        string folderPath = ResolveProjectPath(imageFolderRelativeToProject);
        if (!Directory.Exists(folderPath))
        {
            Debug.LogWarning("[RandomImageProvider] Image folder not found: " + folderPath);
            return;
        }

        SearchOption option = recursive ? SearchOption.AllDirectories : SearchOption.TopDirectoryOnly;
        foreach (string path in Directory.GetFiles(folderPath, "*.*", option))
        {
            if (IsImagePath(path))
            {
                imagePaths.Add(Path.GetFullPath(path));
            }
        }
    }

    void LoadFromManifestFallback()
    {
        string manifestPath = Path.Combine(Application.streamingAssetsPath, manifestFileName);
        if (!File.Exists(manifestPath))
        {
            Debug.LogWarning("[RandomImageProvider] Manifest fallback missing: " + manifestPath);
            return;
        }

        ManifestBatteryList manifest = JsonUtility.FromJson<ManifestBatteryList>(File.ReadAllText(manifestPath));
        if (manifest == null || manifest.batteries == null)
        {
            return;
        }

        foreach (ManifestBattery item in manifest.batteries)
        {
            string path = ResolveProjectPath(item.image_path);
            if (File.Exists(path) && IsImagePath(path))
            {
                imagePaths.Add(path);
            }
        }
    }

    string ResolveProjectPath(string path)
    {
        if (Path.IsPathRooted(path))
        {
            return Path.GetFullPath(path);
        }

        string fromProjectRoot = Path.GetFullPath(Path.Combine(Application.dataPath, "../../../", path));
        if (File.Exists(fromProjectRoot) || Directory.Exists(fromProjectRoot))
        {
            return fromProjectRoot;
        }

        return Path.GetFullPath(Path.Combine(Application.streamingAssetsPath, path));
    }

    static bool IsImagePath(string path)
    {
        string extension = Path.GetExtension(path).ToLowerInvariant();
        return extension == ".png" ||
            extension == ".jpg" ||
            extension == ".jpeg" ||
            extension == ".webp";
    }
}
