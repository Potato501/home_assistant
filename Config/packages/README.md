Packages文件用法参见：https://www.home-assistant.io/docs/configuration/packages/



在`configuration.yaml`文件中加入：

```
homeassistant:
  packages: !include_dir_named packages/
```

文件支持~~**中**~~英文命名（并不支持中文）。感谢B站@柑橘soda踩坑提醒。

