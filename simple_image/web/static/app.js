const { createApp } = Vue;
const { ElMessage } = ElementPlus;

axios.defaults.withCredentials = true;

function resolveApiBasePath() {
  const injected = document
    ?.querySelector('meta[name="simple-image-base-path"]')
    ?.getAttribute("content");
  const normalizedInjected = String(injected || "").trim();
  if (normalizedInjected && normalizedInjected !== "/") {
    return normalizedInjected.endsWith("/")
      ? normalizedInjected.slice(0, -1)
      : normalizedInjected;
  }

  const pathname = new URL(".", window.location.href).pathname;
  if (pathname === "/") {
    return "";
  }
  return pathname.endsWith("/") ? pathname.slice(0, -1) : pathname;
}

const MAX_UPLOAD_COUNT = 10;
const MAX_FILE_SIZE_MB = 10;
const MAX_FILE_SIZE_BYTES = MAX_FILE_SIZE_MB * 1024 * 1024;
const DEFAULT_CLIENT_COMPRESS_ENABLED = true;
const DEFAULT_CLIENT_COMPRESS_QUALITY = 25;
const DEFAULT_CLIENT_MAX_EDGE = 2048;
const MIN_CLIENT_COMPRESS_QUALITY = 5;
const MAX_CLIENT_COMPRESS_QUALITY = 100;
const MIN_CLIENT_MAX_EDGE = 50;
const MAX_CLIENT_MAX_EDGE = 4096;

const I18N_MESSAGES = {
  zh: {
    appName: "简单图床",
    appSubtitle: "Simple Image",
    adminAction: "管理",
    logoutAction: "退出登录",
    tabUpload: "上传图片",
    tabCompress: "压缩图片",
    tabImages: "我的图片",
    loginRequiredUploadTitle: "上传图片需要登录",
    loginRequiredImagesTitle: "查看图片需要登录",
    goLogin: "去登录",
    uploadDropTextPrefix: "粘贴、拖拽图片到此处，或",
    uploadDropTextAction: "点击选择",
    uploadTip: "最多 {count} 张（超出仅保留前 {count} 张），每张不超过 {size}MB",
    clientCompressPanelTitle: "压缩参数",
    clientCompressQualityLabel: "画质",
    clientCompressMaxEdgeLabel: "最长边",
    uploadCompressionTitle: "图片预览",
    uploadCompressHint: "图片上传前会在浏览器中修正方向并压缩，当前压缩率为 {quality} %。",
    localDownloadAction: "下载压缩结果",
    localClearAction: "清空",
    localCompressFailed: "本地压缩失败：{name}",
    previewUnavailable: "无法预览",
    closePreview: "关闭预览",
    tagsCreatablePlaceholder: "标签（可创建）",
    uploadSelectedAction: "上传已选图片",
    uploadSuccessSuffix: "上传成功",
    originalFilenameLabel: "原文件名：{name}",
    previewSizeInfo: "本地处理：{original} -> {compressed}",
    copyLinkAction: "复制链接",
    loginRequiredImagesText: "查看和管理我的图片需要登录。",
    filterByTag: "按标签筛选",
    refreshAction: "刷新",
    emptyImages: "暂无图片",
    monthTitle: "{label}（{count}）",
    uploadTimeLabel: "上传时间：{time}",
    linkLabel: "链接：",
    editTagsPlaceholder: "编辑标签",
    downloadAction: "下载",
    deleteAction: "删除",
    confirmDeleteTitle: "确认删除该图片？",
    updateTagsAction: "更新标签",
    loginDialogTitle: "登录",
    usernameLabel: "用户名",
    usernamePlaceholder: "请输入用户名",
    passwordLabel: "密码",
    passwordPlaceholder: "请输入密码",
    cancelAction: "取消",
    confirmAction: "确定",
    adminDialogTitle: "管理员 · 用户管理",
    newUsernameLabel: "新用户名",
    newUsernamePlaceholder: "例如: alice",
    initialPasswordLabel: "初始密码",
    emailOptionalLabel: "邮箱（可选）",
    createUserAction: "新增用户",
    refreshUsersAction: "刷新用户列表",
    columnUsername: "用户名",
    columnRole: "角色",
    columnCompressPolicy: "压缩策略",
    compressOnWithQuality: "开启 / Q{quality}",
    compressOff: "关闭",
    columnChangePassword: "改密",
    changePasswordAction: "修改密码",
    columnUploadSettings: "压缩设置",
    settingsAction: "设置",
    passwordDialogTitle: "修改用户密码",
    userLabel: "用户",
    newPasswordLabel: "新密码",
    uploadSettingsDialogTitle: "用户上传压缩设置",
    compressEnableLabel: "是否启用压缩",
    compressQualityLabel: "压缩率 Quality (1-95)",
    saveAction: "保存",
    roleAdmin: "admin",
    roleUser: "user",
    needLogin: "请先登录",
    needLoginUpload: "上传图片需要登录",
    needLoginImages: "查看图片需要登录",
    maxSelectCount: "一次最多选择 {count} 张图片",
    maxSelectKeep: "一次最多选择 {count} 张图片，已保留前 {count} 张",
    pastedImagesAdded: "已从剪贴板添加 {count} 张图片",
    pasteImageLimitReached: "最多上传 {count} 张图片，剪贴板中的其余图片未添加",
    copied: "地址已复制",
    copyFailed: "复制失败，请手动复制",
    usernamePasswordRequired: "请输入用户名和密码",
    loginSuccess: "登录成功",
    loginFailed: "登录失败",
    loggedOut: "已退出登录",
    fetchTagsFailed: "获取标签失败",
    fetchImagesFailed: "获取图片列表失败",
    selectImagesFirst: "请先选择图片",
    maxUploadExceeded: "一次最多上传 {count} 张图片",
    oversizedExist: "存在超过 {size}MB 的文件，请移除后再上传",
    uploadPreparationFailed: "存在本地处理失败的图片，请移除后再上传",
    uploadDone: "上传完成",
    uploadFailed: "上传失败",
    tagsUpdated: "标签已更新",
    updateTagsFailed: "更新标签失败",
    deleteSuccess: "删除成功",
    deleteFailed: "删除失败",
    fetchUsersFailed: "获取用户列表失败",
    fillUsernamePassword: "请填写用户名和密码",
    createUserSuccess: "用户创建成功",
    createUserFailed: "创建用户失败",
    fillNewPassword: "请填写新密码",
    passwordUpdated: "密码已更新",
    updatePasswordFailed: "修改密码失败",
    compressQualityRequired: "开启压缩时必须设置压缩率",
    uploadSettingsSaved: "上传设置已保存",
    uploadSettingsSaveFailed: "保存上传设置失败",
    monthLabel: "{year}年{month}月",
    compressionRateInfo: "压缩率：{rate}%",
    localCompressUploadTip: "不限图片数量和文件大小；仅在浏览器本地处理，不会上传到服务器。",
    uploadMonthStart: "开始月份",
    uploadMonthEnd: "结束月份",
    rangeSeparator: "至",
  },
  en: {
    appName: "Simple Image",
    appSubtitle: "Simple Image",
    adminAction: "Admin",
    logoutAction: "Log out",
    tabUpload: "Upload",
    tabCompress: "Compress",
    tabImages: "My Images",
    loginRequiredUploadTitle: "Login required to upload images",
    loginRequiredImagesTitle: "Login required to view images",
    goLogin: "Log in",
    uploadDropTextPrefix: "Paste or drag images here, or",
    uploadDropTextAction: "click to select",
    uploadTip: "Up to {count} images (keeping first {count}); each no larger than {size}MB",
    clientCompressPanelTitle: "Compression settings",
    clientCompressQualityLabel: "Quality",
    clientCompressMaxEdgeLabel: "Max edge",
    uploadCompressionTitle: "Image preview",
    uploadCompressHint: "Images are oriented and compressed in the browser before upload. Current compression rate: {quality}%.",
    localDownloadAction: "Download result",
    localClearAction: "Clear",
    localCompressFailed: "Local compression failed: {name}",
    previewUnavailable: "Preview unavailable",
    closePreview: "Close preview",
    tagsCreatablePlaceholder: "Tags (creatable)",
    uploadSelectedAction: "Upload selected images",
    uploadSuccessSuffix: "uploaded successfully",
    originalFilenameLabel: "Original filename: {name}",
    previewSizeInfo: "Local processing: {original} -> {compressed}",
    copyLinkAction: "Copy link",
    loginRequiredImagesText: "Login is required to view and manage your images.",
    filterByTag: "Filter by tag",
    refreshAction: "Refresh",
    emptyImages: "No images",
    monthTitle: "{label} ({count})",
    uploadTimeLabel: "Uploaded at: {time}",
    linkLabel: "Link:",
    editTagsPlaceholder: "Edit tags",
    downloadAction: "Download",
    deleteAction: "Delete",
    confirmDeleteTitle: "Delete this image?",
    updateTagsAction: "Update tags",
    loginDialogTitle: "Login",
    usernameLabel: "Username",
    usernamePlaceholder: "Enter username",
    passwordLabel: "Password",
    passwordPlaceholder: "Enter password",
    cancelAction: "Cancel",
    confirmAction: "Confirm",
    adminDialogTitle: "Admin · User Management",
    newUsernameLabel: "New username",
    newUsernamePlaceholder: "e.g. alice",
    initialPasswordLabel: "Initial password",
    emailOptionalLabel: "Email (optional)",
    createUserAction: "Create user",
    refreshUsersAction: "Refresh users",
    columnUsername: "Username",
    columnRole: "Role",
    columnCompressPolicy: "Compression",
    compressOnWithQuality: "Enabled / Q{quality}",
    compressOff: "Disabled",
    columnChangePassword: "Password",
    changePasswordAction: "Change password",
    columnUploadSettings: "Upload settings",
    settingsAction: "Settings",
    passwordDialogTitle: "Change User Password",
    userLabel: "User",
    newPasswordLabel: "New password",
    uploadSettingsDialogTitle: "User Upload Compression Settings",
    compressEnableLabel: "Enable compression",
    compressQualityLabel: "Compression Quality (1-95)",
    saveAction: "Save",
    roleAdmin: "admin",
    roleUser: "user",
    needLogin: "Please log in first",
    needLoginUpload: "Login required to upload images",
    needLoginImages: "Login required to view images",
    maxSelectCount: "You can select up to {count} images at once",
    maxSelectKeep: "You can select up to {count} images; only the first {count} are kept",
    pastedImagesAdded: "Added {count} image(s) from the clipboard",
    pasteImageLimitReached: "You can upload up to {count} images; remaining clipboard images were not added",
    copied: "Link copied",
    copyFailed: "Copy failed, please copy manually",
    usernamePasswordRequired: "Please enter username and password",
    loginSuccess: "Login successful",
    loginFailed: "Login failed",
    loggedOut: "Logged out",
    fetchTagsFailed: "Failed to fetch tags",
    fetchImagesFailed: "Failed to fetch image list",
    selectImagesFirst: "Please select images first",
    maxUploadExceeded: "You can upload up to {count} images at once",
    oversizedExist: "Some files exceed {size}MB, please remove them before upload",
    uploadPreparationFailed: "Some images could not be processed locally. Remove them before uploading.",
    uploadDone: "Upload completed",
    uploadFailed: "Upload failed",
    tagsUpdated: "Tags updated",
    updateTagsFailed: "Failed to update tags",
    deleteSuccess: "Deleted successfully",
    deleteFailed: "Delete failed",
    fetchUsersFailed: "Failed to fetch users",
    fillUsernamePassword: "Please fill in username and password",
    createUserSuccess: "User created",
    createUserFailed: "Failed to create user",
    fillNewPassword: "Please enter a new password",
    passwordUpdated: "Password updated",
    updatePasswordFailed: "Failed to update password",
    compressQualityRequired: "Compression quality is required when compression is enabled",
    uploadSettingsSaved: "Upload settings saved",
    uploadSettingsSaveFailed: "Failed to save upload settings",
    monthLabel: "{year}-{month}",
    compressionRateInfo: "Compression rate: {rate}%",
    localCompressUploadTip: "No image-count or file-size limit. Processing is local and never uploads files.",
    uploadMonthStart: "Start month",
    uploadMonthEnd: "End month",
    rangeSeparator: "to",
  },
};

function resolveLocale() {
  const preferred = Array.isArray(navigator.languages) && navigator.languages.length
    ? navigator.languages[0]
    : navigator.language;
  const normalized = String(preferred || "zh").toLowerCase();
  return normalized.startsWith("zh") ? "zh" : "en";
}

function toAbsoluteUrl(input) {
  try {
    return new URL(input, window.location.origin).href;
  } catch (_error) {
    return input;
  }
}

function getFileExtension(name) {
  const matched = String(name || "").toLowerCase().match(/\.([a-z0-9]+)$/);
  return matched ? matched[1] : "";
}

function isHeicFile(file) {
  const ext = getFileExtension(file?.name || "");
  const type = String(file?.type || "").toLowerCase();
  return ["heic", "heif"].includes(ext) || [
    "image/heic",
    "image/heif",
    "image/heic-sequence",
    "image/heif-sequence",
  ].includes(type);
}

async function isHeifContainer(file) {
  if (isHeicFile(file)) {
    return true;
  }
  if (!file || typeof file.slice !== "function") {
    return false;
  }

  const header = new Uint8Array(await file.slice(0, 64).arrayBuffer());
  if (header.length < 12 || String.fromCharCode(...header.slice(4, 8)) !== "ftyp") {
    return false;
  }

  const heifBrands = new Set(["heic", "heix", "hevc", "hevx", "heim", "heis", "mif1", "msf1"]);
  for (let offset = 8; offset + 4 <= header.length; offset += 4) {
    if (heifBrands.has(String.fromCharCode(...header.slice(offset, offset + 4)))) {
      return true;
    }
  }
  return false;
}

function isJpegFile(file) {
  const ext = getFileExtension(file?.name || "");
  const type = String(file?.type || "").toLowerCase();
  return ["jpg", "jpeg", "jpe", "jfif"].includes(ext) || type === "image/jpeg";
}

function isPngFile(file) {
  const ext = getFileExtension(file?.name || "");
  const type = String(file?.type || "").toLowerCase();
  return ext === "png" || type === "image/png";
}

function isWebpFile(file) {
  const ext = getFileExtension(file?.name || "");
  const type = String(file?.type || "").toLowerCase();
  return ext === "webp" || type === "image/webp";
}

function isGifFile(file) {
  const ext = getFileExtension(file?.name || "");
  const type = String(file?.type || "").toLowerCase();
  return ext === "gif" || type === "image/gif";
}

function isSvgFile(file) {
  const ext = getFileExtension(file?.name || "");
  const type = String(file?.type || "").toLowerCase();
  return ext === "svg" || type === "image/svg+xml";
}

function isCanvasProcessableImage(file) {
  const type = String(file?.type || "").toLowerCase();
  if (isHeicFile(file) || isSvgFile(file) || isGifFile(file)) {
    return !isSvgFile(file) && !isGifFile(file);
  }
  return type.startsWith("image/") || isJpegFile(file) || isPngFile(file) || isWebpFile(file);
}

function toJpegFilename(name) {
  const base = String(name || "image").replace(/\.[^/.]+$/, "");
  return `${base}.jpg`;
}

function blobToFile(blob, fileName, type = blob?.type || "application/octet-stream") {
  return new File([blob], fileName, {
    type,
    lastModified: Date.now(),
  });
}

function replaceFileExtension(name, extension) {
  const base = String(name || "image").replace(/\.[^/.]+$/, "");
  return `${base}.${extension}`;
}

function toOutputFilename(name, outputType) {
  if (outputType === "image/jpeg") {
    return toJpegFilename(name);
  }
  if (outputType === "image/png") {
    return replaceFileExtension(name, "png");
  }
  if (outputType === "image/webp") {
    return replaceFileExtension(name, "webp");
  }
  return name || "image";
}

function loadImageFromBlob(blob) {
  return new Promise((resolve, reject) => {
    const objectUrl = URL.createObjectURL(blob);
    const image = new Image();
    image.onload = () => {
      URL.revokeObjectURL(objectUrl);
      resolve(image);
    };
    image.onerror = () => {
      URL.revokeObjectURL(objectUrl);
      reject(new Error("Failed to decode image"));
    };
    image.src = objectUrl;
  });
}

function loadImageWithOrientation(blob) {
  if (typeof window.loadImage !== "function") {
    return loadImageFromBlob(blob);
  }

  return new Promise((resolve, reject) => {
    window.loadImage(
      blob,
      (image) => {
        if (!image || image.type === "error") {
          reject(new Error("Failed to decode image"));
          return;
        }
        resolve(image);
      },
      { canvas: true, orientation: true }
    );
  });
}

async function decodeImageSource(file) {
  let sourceBlob = file;
  if (await isHeifContainer(file)) {
    if (typeof window.heic2any !== "function") {
      throw new Error("HEIC/HEIF decoder is unavailable");
    }

    const converted = await window.heic2any({
      blob: file,
      toType: "image/jpeg",
      quality: 0.92,
    });
    sourceBlob = Array.isArray(converted) ? converted[0] : converted;
    if (!(sourceBlob instanceof Blob)) {
      throw new Error("Failed to convert HEIC/HEIF image");
    }
  }

  return loadImageWithOrientation(sourceBlob);
}

function closeImageSource(imageSource) {
  // No-op for HTMLImageElement; kept for API compatibility.
}

function createRenderCanvas(width, height) {
  if (typeof window.OffscreenCanvas === "function") {
    return new window.OffscreenCanvas(width, height);
  }
  const canvas = document.createElement("canvas");
  canvas.width = width;
  canvas.height = height;
  return canvas;
}

async function canvasToBlob(canvas, type, quality) {
  if (typeof canvas.convertToBlob === "function") {
    return canvas.convertToBlob({ type, quality });
  }
  return new Promise((resolve, reject) => {
    canvas.toBlob(
      (blob) => {
        if (!blob) {
          reject(new Error("Failed to encode image"));
          return;
        }
        resolve(blob);
      },
      type,
      quality
    );
  });
}

function calculateTargetDimensions(width, height, maxEdge) {
  const safeWidth = Math.max(1, Math.round(width || 1));
  const safeHeight = Math.max(1, Math.round(height || 1));
  const safeMaxEdge = Math.max(1, Math.round(maxEdge || 1));
  const longest = Math.max(safeWidth, safeHeight);
  if (longest <= safeMaxEdge) {
    return {
      width: safeWidth,
      height: safeHeight,
      resized: false,
    };
  }

  const ratio = safeMaxEdge / longest;
  return {
    width: Math.max(1, Math.round(safeWidth * ratio)),
    height: Math.max(1, Math.round(safeHeight * ratio)),
    resized: true,
  };
}

function supportsEncoderQuality(type) {
  return type === "image/jpeg" || type === "image/webp";
}

function toCanvasQuality(quality) {
  const safeQuality = Number(quality);
  const normalized = Number.isFinite(safeQuality) ? safeQuality : DEFAULT_CLIENT_COMPRESS_QUALITY;
  const clamped = Math.min(MAX_CLIENT_COMPRESS_QUALITY, Math.max(MIN_CLIENT_COMPRESS_QUALITY, normalized));
  return clamped / 100;
}

function clampMaxEdge(maxEdge) {
  if (maxEdge === null || maxEdge === undefined || maxEdge === "") {
    return null;
  }
  const value = Number(maxEdge);
  if (!Number.isFinite(value)) {
    return DEFAULT_CLIENT_MAX_EDGE;
  }
  return Math.min(MAX_CLIENT_MAX_EDGE, Math.max(MIN_CLIENT_MAX_EDGE, Math.round(value)));
}

function getPreferredOutputType(file, isHeif = false) {
  if (isHeif || isJpegFile(file)) {
    return "image/jpeg";
  }
  if (isWebpFile(file)) {
    return "image/webp";
  }
  if (isPngFile(file)) {
    return "image/png";
  }
  return String(file?.type || "image/jpeg").toLowerCase() || "image/jpeg";
}

async function prepareImageForUpload(file, options = {}) {
  const compressionEnabled = !!options.enabled;
  const canProcess = isCanvasProcessableImage(file);
  const isHeif = await isHeifContainer(file);
  const shouldNormalize = isHeif || isJpegFile(file);
  const shouldCompress = compressionEnabled && canProcess;

  if (!shouldNormalize && !shouldCompress) {
    return {
      file,
      changed: false,
      originalSize: file.size,
      processedSize: file.size,
    };
  }

  let outputType = getPreferredOutputType(file, isHeif);
  let outputName = toOutputFilename(file.name, outputType);

  let imageSource = null;
  try {
    imageSource = await decodeImageSource(file);
    const sourceWidth = imageSource.naturalWidth || imageSource.width;
    const sourceHeight = imageSource.naturalHeight || imageSource.height;
    const maxEdge = clampMaxEdge(options.maxEdge);
    const targetSize = shouldCompress && maxEdge
      ? calculateTargetDimensions(sourceWidth, sourceHeight, maxEdge)
      : { width: sourceWidth, height: sourceHeight, resized: false };

    const needsCanvasRender = shouldNormalize || targetSize.resized || shouldCompress;
    if (!needsCanvasRender) {
      return {
        file,
        changed: false,
        originalSize: file.size,
        processedSize: file.size,
      };
    }

    const canvas = createRenderCanvas(targetSize.width, targetSize.height);
    const ctx = canvas.getContext("2d", { alpha: outputType !== "image/jpeg" }) || canvas.getContext("2d");
    if (!ctx) {
      throw new Error("Canvas 2D not available");
    }
    ctx.imageSmoothingEnabled = true;
    ctx.imageSmoothingQuality = "high";
    if (outputType === "image/jpeg") {
      ctx.fillStyle = "#ffffff";
      ctx.fillRect(0, 0, targetSize.width, targetSize.height);
    }
    ctx.drawImage(imageSource, 0, 0, targetSize.width, targetSize.height);

    const quality = supportsEncoderQuality(outputType)
      ? (shouldCompress ? toCanvasQuality(options.quality) : 0.92)
      : undefined;
    const outputBlob = await canvasToBlob(canvas, outputType, quality);
    const outputFile = blobToFile(outputBlob, outputName, outputType);
    return {
      file: outputFile,
      changed: outputFile.size !== file.size || outputFile.name !== file.name,
      originalSize: file.size,
      processedSize: outputFile.size,
    };
  } finally {
    closeImageSource(imageSource);
  }
}

const LazyThumb = {
  props: {
    src: {
      type: String,
      required: true,
    },
    alt: {
      type: String,
      default: "thumbnail",
    },
    wrapperClass: {
      type: String,
      default: "",
    },
  },
  data() {
    return {
      loaded: false,
      shouldLoad: false,
      observer: null,
    };
  },
  computed: {
    resolvedSrc() {
      return this.shouldLoad ? this.src : "";
    },
    canObserve() {
      return typeof window !== "undefined" && "IntersectionObserver" in window;
    },
  },
  watch: {
    src() {
      this.loaded = false;
      if (!this.canObserve) {
        this.shouldLoad = true;
      }
    },
  },
  mounted() {
    if (!this.canObserve) {
      this.shouldLoad = true;
      return;
    }

    this.observer = new IntersectionObserver(
      (entries) => {
        const entry = entries[0];
        if (entry && entry.isIntersecting) {
          this.shouldLoad = true;
          this.disconnectObserver();
        }
      },
      { rootMargin: "120px 0px" }
    );
    this.observer.observe(this.$el);
  },
  beforeUnmount() {
    this.disconnectObserver();
  },
  methods: {
    disconnectObserver() {
      if (this.observer) {
        this.observer.disconnect();
        this.observer = null;
      }
    },
    handleLoad() {
      this.loaded = true;
    },
    handleError() {
      this.loaded = true;
    },
  },
  template: `
    <div class="thumb-shell" :class="wrapperClass">
      <div v-if="!loaded" class="thumb-skeleton"></div>
      <img
        class="thumb-image"
        :src="resolvedSrc"
        :alt="alt"
        loading="lazy"
        decoding="async"
        @load="handleLoad"
        @error="handleError"
        :style="{ opacity: loaded ? 1 : 0 }"
      />
    </div>
  `,
};

const app = createApp({
  data() {
    return {
      apiBase: resolveApiBasePath(),
      locale: resolveLocale(),
      user: null,

      activeTab: "upload",
      loginLoading: false,
      uploadLoading: false,
      imagesLoading: false,
      adminLoading: false,

      loginForm: {
        username: "",
        password: "",
      },
      loginDialogVisible: false,
      loginReason: "",
      pendingAction: "",

      adminDialogVisible: false,

      createUserForm: {
        username: "",
        password: "",
        email: "",
      },

      passwordDialogVisible: false,
      passwordForm: {
        user_id: "",
        username: "",
        password: "",
      },

      uploadSettingsDialogVisible: false,
      uploadSettingsForm: {
        user_id: "",
        username: "",
        compress_enabled: true,
        compress_quality: 25,
      },

      users: [],
      tags: [],
      images: [],
      monthGroups: [],
      activeMonthGroups: [],
      imageFilterTag: "",
      imageFilterMonths: [],
      imagePage: 1,
      imagePageSize: 20,
      imageTotal: 0,

      fileList: [],
      uploadItems: [],
      uploadResults: [],
      uploadPreviewBuildToken: 0,
      compressFileList: [],
      compressItems: [],
      compressBuildToken: 0,
      clientCompressQuality: DEFAULT_CLIENT_COMPRESS_QUALITY,
      clientCompressMaxEdge: DEFAULT_CLIENT_MAX_EDGE,
      compressBaselineQuality: DEFAULT_CLIENT_COMPRESS_QUALITY,
      compressBaselineMaxEdge: DEFAULT_CLIENT_MAX_EDGE,
      imagePreviewVisible: false,
      imagePreviewUrl: "",
      imagePreviewName: "",

      maxUploadCount: MAX_UPLOAD_COUNT,
      maxFileSizeMB: MAX_FILE_SIZE_MB,
    };
  },
  computed: {
    userUploadQuality() {
      const quality = Number(this.user?.compress_quality);
      if (!Number.isFinite(quality)) {
        return DEFAULT_CLIENT_COMPRESS_QUALITY;
      }
      return Math.min(MAX_CLIENT_COMPRESS_QUALITY, Math.max(1, Math.round(quality)));
    },
    compressOptionsChanged() {
      return this.clientCompressQuality !== this.compressBaselineQuality
        || this.clientCompressMaxEdge !== this.compressBaselineMaxEdge;
    },
  },
  methods: {
    t(key, params = {}) {
      const table = I18N_MESSAGES[this.locale] || I18N_MESSAGES.zh;
      const fallback = I18N_MESSAGES.zh;
      const template = table[key] || fallback[key] || key;
      return template.replace(/\{(\w+)\}/g, (_, name) => String(params[name] ?? ""));
    },

    roleLabel(isAdmin) {
      return isAdmin ? this.t("roleAdmin") : this.t("roleUser");
    },

    requestLogin(reason = "") {
      this.loginReason = reason || this.t("needLogin");
      this.loginDialogVisible = true;
    },

    monthGroupLabel(year, month) {
      return this.t("monthLabel", { year, month });
    },

    setDocumentTitle() {
      document.title = this.t("appName");
      document.documentElement.lang = this.locale === "zh" ? "zh-CN" : "en";
    },

    requestLoginForPane(paneName) {
      this.requestLogin(paneName === "upload" ? this.t("needLoginUpload") : this.t("needLoginImages"));
    },

    requestUploadLogin() {
      this.requestLogin(this.t("needLoginUpload"));
    },

    requestImagesLogin() {
      this.requestLogin(this.t("needLoginImages"));
    },

    onImageFilterChange() {
      this.imagePage = 1;
      this.fetchMyImages();
    },

    compressionRate(originalSize, processedSize) {
      if (!originalSize || originalSize <= 0 || !Number.isFinite(processedSize)) {
        return 100;
      }
      return Math.max(0, Math.round((processedSize / originalSize) * 100));
    },

    openImagePreview(url, name) {
      this.imagePreviewUrl = url;
      this.imagePreviewName = name || "";
      this.imagePreviewVisible = true;
    },

    onImagePageChange(page) {
      this.imagePage = page;
      this.fetchMyImages();
    },

    onTabClick(tab) {
      const paneName = tab?.paneName || tab?.props?.name;
      if (!this.user && (paneName === "upload" || paneName === "images")) {
        this.pendingAction = paneName;
        this.requestLoginForPane(paneName);
      }
    },

    async openAdminDialog() {
      if (!this.user || !this.user.is_admin) {
        return;
      }
      this.adminDialogVisible = true;
      await this.loadUsers();
    },

    formatDate(value) {
      if (!value) {
        return "-";
      }
      return new Date(value).toLocaleString();
    },

    formatSize(size) {
      if (!Number.isFinite(size)) {
        return "0 B";
      }
      if (size < 1024) {
        return `${size} B`;
      }
      if (size < 1024 * 1024) {
        return `${(size / 1024).toFixed(1)} KB`;
      }
      return `${(size / (1024 * 1024)).toFixed(2)} MB`;
    },

    savePercent(img) {
      if (!img || !img.original_size || img.original_size <= 0) {
        return 0;
      }
      const saved = img.original_size - (img.compressed_size || 0);
      return Math.max(0, Math.round((saved / img.original_size) * 100));
    },

    async onFileChange(_file, latestFileList) {
      this.fileList = this.validateFileList(latestFileList);
      await this.syncUploadItems();
    },

    async onFileRemove(_file, latestFileList) {
      this.fileList = this.validateFileList(latestFileList, false);
      await this.syncUploadItems();
    },

    onUploadExceed() {
      ElMessage.error(this.t("maxSelectCount", { count: this.maxUploadCount }));
    },

    isTextInputTarget(target) {
      const element = target instanceof Element ? target : null;
      return !!element?.closest('input, textarea, [contenteditable="true"], [contenteditable=""]');
    },

    async handlePaste(event) {
      if (!["upload", "compress"].includes(this.activeTab) || this.isTextInputTarget(event.target)) {
        return;
      }

      const files = Array.from(event.clipboardData?.items || [])
        .filter((item) => item.kind === "file" && item.type.startsWith("image/"))
        .map((item) => item.getAsFile())
        .filter(Boolean);
      if (!files.length) {
        return;
      }

      event.preventDefault();
      const isUpload = this.activeTab === "upload";
      const remaining = isUpload ? Math.max(0, this.maxUploadCount - this.fileList.length) : files.length;
      const pasted = files.slice(0, remaining).map((file, index) => ({
        name: file.name || `clipboard-${Date.now()}-${index}.png`,
        percentage: 0,
        raw: file,
        size: file.size,
        status: "ready",
        uid: `clipboard-${Date.now()}-${index}-${Math.random().toString(36).slice(2)}`,
      }));
      if (!pasted.length) {
        ElMessage.error(this.t("pasteImageLimitReached", { count: this.maxUploadCount }));
        return;
      }

      if (isUpload) {
        this.fileList = [...this.fileList, ...pasted];
        await this.syncUploadItems();
      } else {
        this.compressFileList = [...this.compressFileList, ...pasted];
        await this.syncCompressItems();
      }
      ElMessage.success(this.t("pastedImagesAdded", { count: pasted.length }));
      if (isUpload && pasted.length < files.length) {
        ElMessage.warning(this.t("pasteImageLimitReached", { count: this.maxUploadCount }));
      }
    },

    async onCompressFileChange(_file, latestFileList) {
      this.compressFileList = this.validateFileList(latestFileList, false, false);
      await this.syncCompressItems();
    },

    async onCompressFileRemove(_file, latestFileList) {
      this.compressFileList = this.validateFileList(latestFileList, false, false);
      await this.syncCompressItems();
    },

    onCompressExceed() {
      ElMessage.error(this.t("maxSelectCount", { count: this.maxUploadCount }));
    },

    async refreshCompressItemsAfterOptionsChange() {
      if (!this.compressFileList.length) {
        return;
      }
      await this.syncCompressItems();
      this.compressBaselineQuality = this.clientCompressQuality;
      this.compressBaselineMaxEdge = this.clientCompressMaxEdge;
    },

    async refreshUploadItemsAfterOptionsChange() {
      if (!this.fileList.length) {
        return;
      }
      await this.syncUploadItems();
    },

    buildClientCompressionOptions() {
      return {
        enabled: true,
        quality: this.clientCompressQuality,
        maxEdge: this.clientCompressMaxEdge,
      };
    },

    validateFileList(fileList, showMessage = true, limitCount = true) {
      const valid = [];

      for (const item of fileList || []) {
        if (limitCount && valid.length >= this.maxUploadCount) {
          continue;
        }
        const raw = item?.raw;
        if (!raw) {
          continue;
        }
        valid.push(item);
      }

      if (showMessage) {
        if (limitCount && (fileList || []).length > this.maxUploadCount) {
          ElMessage.error(this.t("maxSelectKeep", { count: this.maxUploadCount }));
        }
      }

      return valid;
    },

    imageUrl(imageId) {
      return toAbsoluteUrl(`${this.apiBase}/image/${imageId}`);
    },

    thumbnailUrl(imageId, size = 160) {
      return toAbsoluteUrl(`${this.apiBase}/thumbnail/${imageId}?size=${size}`);
    },

    downloadUrl(imageId) {
      return toAbsoluteUrl(`${this.apiBase}/download/${imageId}`);
    },

    buildMonthGroups(items) {
      const groupMap = new Map();
      for (const img of items || []) {
        const date = new Date(img.upload_time);
        const year = date.getFullYear();
        const month = String(date.getMonth() + 1).padStart(2, "0");
        const key = `${year}-${month}`;
        if (!groupMap.has(key)) {
          groupMap.set(key, {
            key,
            label: this.monthGroupLabel(year, month),
            items: [],
          });
        }
        groupMap.get(key).items.push(img);
      }
      return Array.from(groupMap.values());
    },

    async copyText(text) {
      if (!text) {
        return;
      }
      try {
        if (navigator?.clipboard?.writeText) {
          await navigator.clipboard.writeText(text);
        } else {
          const textarea = document.createElement("textarea");
          textarea.value = text;
          textarea.setAttribute("readonly", "readonly");
          textarea.style.position = "fixed";
          textarea.style.left = "-9999px";
          document.body.appendChild(textarea);
          textarea.select();
          document.execCommand("copy");
          document.body.removeChild(textarea);
        }
        ElMessage.success(this.t("copied"));
      } catch (_error) {
        ElMessage.error(this.t("copyFailed"));
      }
    },

    async syncUploadItems() {
      const currentToken = ++this.uploadPreviewBuildToken;
      const existingTags = new Map(this.uploadItems.map((item) => [item.uid, item.tags]));
      this.cleanupUploadObjectUrls();

      const nextItems = [];
      for (const item of this.fileList) {
        const raw = item?.raw;
        if (!raw) {
          continue;
        }
        try {
          const prepared = await prepareImageForUpload(raw, {
            enabled: !!this.user?.compress_enabled,
            quality: this.userUploadQuality,
            maxEdge: null,
          });
          if (currentToken !== this.uploadPreviewBuildToken) {
            return;
          }
          nextItems.push({
            uid: item.uid,
            file: prepared.file,
            preview: URL.createObjectURL(prepared.file),
            tags: existingTags.get(item.uid) || [],
            previewFailed: false,
            originalSize: prepared.originalSize,
            processedSize: prepared.processedSize,
            changed: prepared.changed,
            error: "",
          });
        } catch (_error) {
          if (currentToken !== this.uploadPreviewBuildToken) {
            return;
          }
          nextItems.push({
            uid: item.uid,
            file: null,
            preview: "",
            tags: existingTags.get(item.uid) || [],
            previewFailed: true,
            originalSize: raw.size,
            processedSize: raw.size,
            changed: false,
            error: this.t("localCompressFailed", { name: raw.name || "Unnamed file" }),
            failedName: raw.name || "Unnamed file",
          });
        }
      }

      if (currentToken !== this.uploadPreviewBuildToken) {
        return;
      }
      this.uploadItems = nextItems;
    },

    async syncCompressItems() {
      const currentToken = ++this.compressBuildToken;
      this.cleanupCompressObjectUrls();

      const nextItems = [];
      for (const item of this.compressFileList) {
        if (!item?.raw) {
          continue;
        }
        try {
          const prepared = await prepareImageForUpload(item.raw, this.buildClientCompressionOptions());
          if (currentToken !== this.compressBuildToken) {
            return;
          }
          nextItems.push({
            uid: item.uid,
            file: prepared.file,
            preview: URL.createObjectURL(prepared.file),
            originalSize: prepared.originalSize,
            processedSize: prepared.processedSize,
            changed: prepared.changed,
            error: "",
          });
        } catch (error) {
          if (currentToken !== this.compressBuildToken) {
            return;
          }
          const name = item.raw.name || "Unnamed file";
          nextItems.push({
            uid: item.uid,
            file: null,
            preview: "",
            originalSize: item.raw.size,
            processedSize: item.raw.size,
            changed: false,
            error: error?.message || this.t("localCompressFailed", { name }),
            failedName: name,
          });
        }
      }

      this.compressItems = nextItems;
    },

    cleanupUploadObjectUrls() {
      this.uploadItems.forEach((item) => {
        if (item.preview) {
          URL.revokeObjectURL(item.preview);
        }
      });
    },

    cleanupCompressObjectUrls() {
      this.compressItems.forEach((item) => {
        if (item.preview) {
          URL.revokeObjectURL(item.preview);
        }
      });
    },

    clearCompressItems() {
      this.compressFileList = [];
      this.cleanupCompressObjectUrls();
      this.compressItems = [];
    },

    handleUploadPreviewError(item) {
      if (!item) {
        return;
      }
      item.previewFailed = true;
    },

    downloadCompressedItem(item) {
      if (!item?.file || !item?.preview) {
        ElMessage.warning(this.t("previewUnavailable"));
        return;
      }
      const anchor = document.createElement("a");
      anchor.href = item.preview;
      anchor.download = item.file.name || "compressed-image";
      anchor.rel = "noopener";
      anchor.style.display = "none";
      document.body.appendChild(anchor);
      anchor.click();
      document.body.removeChild(anchor);
    },

    async login() {
      if (!this.loginForm.username || !this.loginForm.password) {
        ElMessage.warning(this.t("usernamePasswordRequired"));
        return;
      }

      this.loginLoading = true;
      try {
        const res = await axios.post(`${this.apiBase}/auth/login`, {
          username: this.loginForm.username,
          password: this.loginForm.password,
        });

        this.user = res.data.user;
        this.loginForm.password = "";
        this.loginDialogVisible = false;
        ElMessage.success(this.t("loginSuccess"));
        await this.onAuthenticated();
        if (this.pendingAction === "images") {
          this.activeTab = "images";
          await this.fetchMyImages();
        } else if (this.pendingAction === "upload") {
          this.activeTab = "upload";
        }
        this.pendingAction = "";
      } catch (error) {
        ElMessage.error(error?.response?.data?.detail || this.t("loginFailed"));
      } finally {
        this.loginLoading = false;
      }
    },

    async logout() {
      try {
        await axios.post(`${this.apiBase}/auth/logout`);
      } catch (_error) {
        // Ignore server-side logout error and always clear local auth state.
      } finally {
        this.user = null;
        this.loginDialogVisible = false;
        this.adminDialogVisible = false;
        this.pendingAction = "";
        this.users = [];
        this.images = [];
        this.monthGroups = [];
        this.activeMonthGroups = [];
        this.tags = [];
        this.uploadResults = [];
        this.fileList = [];
        this.cleanupUploadObjectUrls();
        this.uploadItems = [];
        this.clearCompressItems();
        ElMessage.success(this.t("loggedOut"));
      }
    },

    async fetchMe() {
      const res = await axios.get(`${this.apiBase}/auth/me`);
      this.user = res.data;
      return this.user;
    },

    async onAuthenticated() {
      await Promise.all([this.fetchTags(), this.fetchMyImages()]);
      if (this.fileList.length) {
        await this.syncUploadItems();
      }
      if (this.user && this.user.is_admin) {
        await this.loadUsers();
      }
    },

    async fetchTags() {
      if (!this.user) {
        this.tags = [];
        return;
      }
      try {
        const res = await axios.get(`${this.apiBase}/tags/me`);
        this.tags = res.data || [];
      } catch (error) {
        ElMessage.error(error?.response?.data?.detail || this.t("fetchTagsFailed"));
      }
    },

    async fetchMyImages() {
      if (!this.user) {
        this.images = [];
        this.monthGroups = [];
        this.activeMonthGroups = [];
        this.imageTotal = 0;
        this.imagePage = 1;
        if (this.activeTab === "images") {
          this.pendingAction = "images";
          this.requestImagesLogin();
        }
        return;
      }

      this.imagesLoading = true;
      try {
        const res = await axios.get(`${this.apiBase}/images/me/page`, {
          params: {
            ...(this.imageFilterTag ? { tag: this.imageFilterTag } : {}),
            ...(this.imageFilterMonths?.[0] ? { upload_month_start: this.imageFilterMonths[0] } : {}),
            ...(this.imageFilterMonths?.[1] ? { upload_month_end: this.imageFilterMonths[1] } : {}),
            page: this.imagePage,
            page_size: this.imagePageSize,
          },
        });
        const items = res?.data?.items || [];
        const total = Number(res?.data?.total || 0);
        const sortedImages = items
          .slice()
          .sort((a, b) => new Date(b.upload_time).getTime() - new Date(a.upload_time).getTime())
          .map((img) => ({
            ...img,
            _editTags: Array.isArray(img.tags) ? [...img.tags] : [],
          }));

        if (!sortedImages.length && total > 0 && this.imagePage > 1) {
          this.imagePage -= 1;
          await this.fetchMyImages();
          return;
        }

        this.images = sortedImages;
        this.imageTotal = total;
        this.monthGroups = this.buildMonthGroups(sortedImages);
        this.activeMonthGroups = this.monthGroups.map((group) => group.key);
      } catch (error) {
        ElMessage.error(error?.response?.data?.detail || this.t("fetchImagesFailed"));
      } finally {
        this.imagesLoading = false;
      }
    },

    async uploadAll() {
      if (!this.user) {
        this.pendingAction = "upload";
        this.requestUploadLogin();
        return;
      }
      if (!this.uploadItems.length) {
        ElMessage.warning(this.t("selectImagesFirst"));
        return;
      }
      if (this.uploadItems.length > this.maxUploadCount) {
        ElMessage.error(this.t("maxUploadExceeded", { count: this.maxUploadCount }));
        return;
      }

      if (this.uploadItems.some((item) => !item?.file || item.error)) {
        ElMessage.error(this.t("uploadPreparationFailed"));
        return;
      }

      const oversized = this.uploadItems.find((item) => item?.file?.size > MAX_FILE_SIZE_BYTES);
      if (oversized) {
        ElMessage.error(this.t("oversizedExist", { size: this.maxFileSizeMB }));
        return;
      }

      this.uploadLoading = true;
      this.uploadResults = [];
      try {
        for (const item of this.uploadItems) {
          const form = new FormData();
          form.append("file", item.file);
          form.append("tags", JSON.stringify(item.tags || []));
          form.append("client_original_size", String(item.originalSize));

          const res = await axios.post(`${this.apiBase}/upload`, form, {
            headers: {
              "Content-Type": "multipart/form-data",
            },
          });
          this.uploadResults.push({
            ...res.data,
            tags: item.tags || [],
          });
        }

        this.fileList = [];
        this.cleanupUploadObjectUrls();
        this.uploadItems = [];
        ElMessage.success(this.t("uploadDone"));
        await Promise.all([this.fetchTags(), this.fetchMyImages()]);
      } catch (error) {
        ElMessage.error(error?.response?.data?.detail || this.t("uploadFailed"));
      } finally {
        this.uploadLoading = false;
      }
    },

    async updateTags(img) {
      if (!this.user) {
        ElMessage.warning(this.t("needLogin"));
        return;
      }
      try {
        await axios.put(
          `${this.apiBase}/update-tags/${img.id}`,
          { tags: img._editTags || [] }
        );
        ElMessage.success(this.t("tagsUpdated"));
        await Promise.all([this.fetchTags(), this.fetchMyImages()]);
      } catch (error) {
        ElMessage.error(error?.response?.data?.detail || this.t("updateTagsFailed"));
      }
    },

    async deleteImage(img) {
      if (!this.user) {
        ElMessage.warning(this.t("needLogin"));
        return;
      }
      try {
        await axios.delete(`${this.apiBase}/delete-image/${img.id}`);
        ElMessage.success(this.t("deleteSuccess"));
        await Promise.all([this.fetchTags(), this.fetchMyImages()]);
      } catch (error) {
        ElMessage.error(error?.response?.data?.detail || this.t("deleteFailed"));
      }
    },

    downloadImage(img) {
      if (!img?.id) {
        return;
      }
      const anchor = document.createElement("a");
      anchor.href = this.downloadUrl(img.id);
      anchor.rel = "noopener";
      anchor.style.display = "none";
      document.body.appendChild(anchor);
      anchor.click();
      document.body.removeChild(anchor);
    },

    async loadUsers() {
      if (!this.user || !this.user.is_admin) {
        return;
      }
      this.adminLoading = true;
      try {
        const res = await axios.get(`${this.apiBase}/admin/users`);
        this.users = res.data || [];
      } catch (error) {
        ElMessage.error(error?.response?.data?.detail || this.t("fetchUsersFailed"));
      } finally {
        this.adminLoading = false;
      }
    },

    async createUser() {
      if (!this.user || !this.user.is_admin) {
        return;
      }
      if (!this.createUserForm.username || !this.createUserForm.password) {
        ElMessage.warning(this.t("fillUsernamePassword"));
        return;
      }

      this.adminLoading = true;
      try {
        await axios.post(
          `${this.apiBase}/admin/users`,
          {
            username: this.createUserForm.username,
            password: this.createUserForm.password,
            email: this.createUserForm.email || null,
          }
        );

        this.createUserForm = { username: "", password: "", email: "" };
        ElMessage.success(this.t("createUserSuccess"));
        await this.loadUsers();
      } catch (error) {
        ElMessage.error(error?.response?.data?.detail || this.t("createUserFailed"));
      } finally {
        this.adminLoading = false;
      }
    },

    openPasswordDialog(row) {
      this.passwordForm = {
        user_id: row.id,
        username: row.username,
        password: "",
      };
      this.passwordDialogVisible = true;
    },

    async updatePassword() {
      if (!this.passwordForm.user_id || !this.passwordForm.password) {
        ElMessage.warning(this.t("fillNewPassword"));
        return;
      }

      this.adminLoading = true;
      try {
        await axios.put(
          `${this.apiBase}/admin/users/${this.passwordForm.user_id}/password`,
          { password: this.passwordForm.password }
        );
        this.passwordDialogVisible = false;
        ElMessage.success(this.t("passwordUpdated"));
      } catch (error) {
        ElMessage.error(error?.response?.data?.detail || this.t("updatePasswordFailed"));
      } finally {
        this.adminLoading = false;
      }
    },

    openUploadSettingsDialog(row) {
      this.uploadSettingsForm = {
        user_id: row.id,
        username: row.username,
        compress_enabled: !!row.compress_enabled,
        compress_quality: Number(row.compress_quality || 25),
      };
      this.uploadSettingsDialogVisible = true;
    },

    async updateUploadSettings() {
      if (!this.uploadSettingsForm.user_id) {
        return;
      }
      if (this.uploadSettingsForm.compress_enabled && !this.uploadSettingsForm.compress_quality) {
        ElMessage.warning(this.t("compressQualityRequired"));
        return;
      }

      this.adminLoading = true;
      try {
        await axios.put(
          `${this.apiBase}/admin/users/${this.uploadSettingsForm.user_id}/upload-settings`,
          {
            compress_enabled: this.uploadSettingsForm.compress_enabled,
            compress_quality: this.uploadSettingsForm.compress_enabled
              ? this.uploadSettingsForm.compress_quality
              : null,
          }
        );
        this.uploadSettingsDialogVisible = false;
        ElMessage.success(this.t("uploadSettingsSaved"));
        await this.loadUsers();
      } catch (error) {
        ElMessage.error(error?.response?.data?.detail || this.t("uploadSettingsSaveFailed"));
      } finally {
        this.adminLoading = false;
      }
    },

    async init() {
      this.setDocumentTitle();
      try {
        await this.fetchMe();
        await this.onAuthenticated();
      } catch (_error) {
        this.user = null;
      }
    },
  },
  async mounted() {
    window.addEventListener("paste", this.handlePaste);
    await this.init();
    const boot = document.getElementById("app-boot");
    if (boot) {
      boot.classList.add("done");
      window.setTimeout(() => {
        boot.remove();
      }, 220);
    }
  },
  beforeUnmount() {
    window.removeEventListener("paste", this.handlePaste);
    this.cleanupUploadObjectUrls();
    this.cleanupCompressObjectUrls();
  },
});

app.component("lazy-thumb", LazyThumb);
app.use(ElementPlus).mount("#app");
