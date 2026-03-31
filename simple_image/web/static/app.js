const { createApp } = Vue;
const { ElMessage } = ElementPlus;

axios.defaults.withCredentials = true;

function resolveApiBasePath() {
  const pathname = new URL(".", window.location.href).pathname;
  if (pathname === "/") {
    return "";
  }
  return pathname.endsWith("/") ? pathname.slice(0, -1) : pathname;
}

const MAX_UPLOAD_COUNT = 5;
const MAX_FILE_SIZE_MB = 10;
const MAX_FILE_SIZE_BYTES = MAX_FILE_SIZE_MB * 1024 * 1024;

const I18N_MESSAGES = {
  zh: {
    appName: "简单图床",
    appSubtitle: "Simple Image",
    adminAction: "管理",
    logoutAction: "退出登录",
    tabUpload: "上传图片",
    tabImages: "我的图片",
    loginRequiredUploadTitle: "上传图片需要登录",
    loginRequiredImagesTitle: "查看图片需要登录",
    goLogin: "去登录",
    uploadDropTextPrefix: "拖拽图片到此处，或",
    uploadDropTextAction: "点击选择",
    uploadTip: "最多 {count} 张（超出仅保留前 {count} 张），每张不超过 {size}MB",
    tagsCreatablePlaceholder: "标签（可创建）",
    uploadSelectedAction: "上传已选图片",
    uploadSuccessSuffix: "上传成功",
    originalFilenameLabel: "原文件名：{name}",
    copyLinkAction: "复制链接",
    loginRequiredImagesText: "查看和管理我的图片需要登录。",
    filterByTag: "按标签筛选",
    refreshAction: "刷新",
    emptyImages: "暂无图片",
    monthTitle: "{label}（{count}）",
    uploadTimeLabel: "上传时间：{time}",
    linkLabel: "链接：",
    compressInfo: "压缩：{original} -> {compressed}（节省 {percent}%）",
    editTagsPlaceholder: "编辑标签",
    downloadAction: "下载",
    deleteAction: "删除",
    confirmDeleteTitle: "确认删除该图片？",
    updateTagsAction: "更新标签",
    loginDialogTitle: "登录",
    loginHintDefault: "登录后可进行该操作",
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
    fileTooLargeRemoved: "{files} 超过 {size}MB，已移除",
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
  },
  en: {
    appName: "Simple Image",
    appSubtitle: "Simple Image",
    adminAction: "Admin",
    logoutAction: "Log out",
    tabUpload: "Upload",
    tabImages: "My Images",
    loginRequiredUploadTitle: "Login required to upload images",
    loginRequiredImagesTitle: "Login required to view images",
    goLogin: "Log in",
    uploadDropTextPrefix: "Drag images here, or",
    uploadDropTextAction: "click to select",
    uploadTip: "Up to {count} images (keeping first {count}); each no larger than {size}MB",
    tagsCreatablePlaceholder: "Tags (creatable)",
    uploadSelectedAction: "Upload selected images",
    uploadSuccessSuffix: "uploaded successfully",
    originalFilenameLabel: "Original filename: {name}",
    copyLinkAction: "Copy link",
    loginRequiredImagesText: "Login is required to view and manage your images.",
    filterByTag: "Filter by tag",
    refreshAction: "Refresh",
    emptyImages: "No images",
    monthTitle: "{label} ({count})",
    uploadTimeLabel: "Uploaded at: {time}",
    linkLabel: "Link:",
    compressInfo: "Compression: {original} -> {compressed} (saved {percent}%)",
    editTagsPlaceholder: "Edit tags",
    downloadAction: "Download",
    deleteAction: "Delete",
    confirmDeleteTitle: "Delete this image?",
    updateTagsAction: "Update tags",
    loginDialogTitle: "Login",
    loginHintDefault: "Log in to continue",
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
    fileTooLargeRemoved: "{files} exceed {size}MB and were removed",
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

      fileList: [],
      uploadItems: [],
      uploadResults: [],

      maxUploadCount: MAX_UPLOAD_COUNT,
      maxFileSizeMB: MAX_FILE_SIZE_MB,
    };
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

    onFileChange(_file, latestFileList) {
      this.fileList = this.validateFileList(latestFileList);
      this.syncUploadItems();
    },

    onFileRemove(_file, latestFileList) {
      this.fileList = this.validateFileList(latestFileList, false);
      this.syncUploadItems();
    },

    onUploadExceed() {
      ElMessage.error(this.t("maxSelectCount", { count: this.maxUploadCount }));
    },

    validateFileList(fileList, showMessage = true) {
      const valid = [];
      const oversizedNames = [];

      for (const item of fileList || []) {
        if (valid.length >= this.maxUploadCount) {
          continue;
        }
        const raw = item?.raw;
        if (!raw) {
          continue;
        }
        if (raw.size > MAX_FILE_SIZE_BYTES) {
          oversizedNames.push(raw.name || "Unnamed file");
          continue;
        }
        valid.push(item);
      }

      if (showMessage) {
        if ((fileList || []).length > this.maxUploadCount) {
          ElMessage.error(this.t("maxSelectKeep", { count: this.maxUploadCount }));
        }
        if (oversizedNames.length) {
          const shown = oversizedNames.slice(0, 2).join(", ");
          const suffix = oversizedNames.length > 2 ? " ..." : "";
          ElMessage.error(this.t("fileTooLargeRemoved", { files: `${shown}${suffix}`, size: this.maxFileSizeMB }));
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

    syncUploadItems() {
      const existingTags = new Map(this.uploadItems.map((item) => [item.uid, item.tags]));
      this.cleanupObjectUrls();

      this.uploadItems = this.fileList
        .map((item) => {
          if (!item.raw) {
            return null;
          }
          return {
            uid: item.uid,
            file: item.raw,
            preview: URL.createObjectURL(item.raw),
            tags: existingTags.get(item.uid) || [],
          };
        })
        .filter(Boolean);
    },

    cleanupObjectUrls() {
      this.uploadItems.forEach((item) => {
        if (item.preview) {
          URL.revokeObjectURL(item.preview);
        }
      });
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
        if (this.activeTab === "images") {
          this.pendingAction = "images";
          this.requestImagesLogin();
        }
        return;
      }

      this.imagesLoading = true;
      try {
        const res = await axios.get(`${this.apiBase}/images/me`, {
          params: this.imageFilterTag ? { tag: this.imageFilterTag } : {},
        });
        const sortedImages = (res.data || [])
          .slice()
          .sort((a, b) => new Date(b.upload_time).getTime() - new Date(a.upload_time).getTime())
          .map((img) => ({
          ...img,
          _editTags: Array.isArray(img.tags) ? [...img.tags] : [],
        }));
        this.images = sortedImages;
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
        this.cleanupObjectUrls();
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
    await this.init();
  },
  beforeUnmount() {
    this.cleanupObjectUrls();
  },
});

app.component("lazy-thumb", LazyThumb);
app.use(ElementPlus).mount("#app");
