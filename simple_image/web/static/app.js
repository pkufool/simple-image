const { createApp } = Vue;
const { ElMessage } = ElementPlus;

axios.defaults.withCredentials = true;

createApp({
  data() {
    return {
      apiBase: window.location.origin,
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
      imageFilterTag: "",

      fileList: [],
      uploadItems: [],
      uploadResults: [],
    };
  },
  methods: {
    requestLogin(reason = "请先登录") {
      this.loginReason = reason;
      this.loginDialogVisible = true;
    },

    onTabClick(tab) {
      const paneName = tab?.paneName || tab?.props?.name;
      if (!this.user && (paneName === "upload" || paneName === "images")) {
        this.pendingAction = paneName;
        this.requestLogin(paneName === "upload" ? "上传图片需要登录" : "查看图片需要登录");
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
      this.fileList = latestFileList;
      this.syncUploadItems();
    },

    onFileRemove(_file, latestFileList) {
      this.fileList = latestFileList;
      this.syncUploadItems();
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
        ElMessage.warning("请输入用户名和密码");
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
        ElMessage.success("登录成功");
        await this.onAuthenticated();
        if (this.pendingAction === "images") {
          this.activeTab = "images";
          await this.fetchMyImages();
        } else if (this.pendingAction === "upload") {
          this.activeTab = "upload";
        }
        this.pendingAction = "";
      } catch (error) {
        ElMessage.error(error?.response?.data?.detail || "登录失败");
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
        this.tags = [];
        this.uploadResults = [];
        ElMessage.success("已退出登录");
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
        ElMessage.error(error?.response?.data?.detail || "获取标签失败");
      }
    },

    async fetchMyImages() {
      if (!this.user) {
        this.images = [];
        if (this.activeTab === "images") {
          this.pendingAction = "images";
          this.requestLogin("查看图片需要登录");
        }
        return;
      }

      this.imagesLoading = true;
      try {
        const res = await axios.get(`${this.apiBase}/images/me`, {
          params: this.imageFilterTag ? { tag: this.imageFilterTag } : {},
        });
        this.images = (res.data || []).map((img) => ({
          ...img,
          _editTags: Array.isArray(img.tags) ? [...img.tags] : [],
        }));
      } catch (error) {
        ElMessage.error(error?.response?.data?.detail || "获取图片列表失败");
      } finally {
        this.imagesLoading = false;
      }
    },

    async uploadAll() {
      if (!this.user) {
        this.pendingAction = "upload";
        this.requestLogin("上传图片需要登录");
        return;
      }
      if (!this.uploadItems.length) {
        ElMessage.warning("请先选择图片");
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
          this.uploadResults.push(res.data);
        }

        this.fileList = [];
        this.cleanupObjectUrls();
        this.uploadItems = [];
        ElMessage.success("上传完成");
        await Promise.all([this.fetchTags(), this.fetchMyImages()]);
      } catch (error) {
        ElMessage.error(error?.response?.data?.detail || "上传失败");
      } finally {
        this.uploadLoading = false;
      }
    },

    async updateTags(img) {
      if (!this.user) {
        ElMessage.warning("请先登录");
        return;
      }
      try {
        await axios.put(
          `${this.apiBase}/update-tags/${img.id}`,
          { tags: img._editTags || [] }
        );
        ElMessage.success("标签已更新");
        await Promise.all([this.fetchTags(), this.fetchMyImages()]);
      } catch (error) {
        ElMessage.error(error?.response?.data?.detail || "更新标签失败");
      }
    },

    async deleteImage(img) {
      if (!this.user) {
        ElMessage.warning("请先登录");
        return;
      }
      try {
        await axios.delete(`${this.apiBase}/delete-image/${img.id}`);
        ElMessage.success("删除成功");
        await Promise.all([this.fetchTags(), this.fetchMyImages()]);
      } catch (error) {
        ElMessage.error(error?.response?.data?.detail || "删除失败");
      }
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
        ElMessage.error(error?.response?.data?.detail || "获取用户列表失败");
      } finally {
        this.adminLoading = false;
      }
    },

    async createUser() {
      if (!this.user || !this.user.is_admin) {
        return;
      }
      if (!this.createUserForm.username || !this.createUserForm.password) {
        ElMessage.warning("请填写用户名和密码");
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
        ElMessage.success("用户创建成功");
        await this.loadUsers();
      } catch (error) {
        ElMessage.error(error?.response?.data?.detail || "创建用户失败");
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
        ElMessage.warning("请填写新密码");
        return;
      }

      this.adminLoading = true;
      try {
        await axios.put(
          `${this.apiBase}/admin/users/${this.passwordForm.user_id}/password`,
          { password: this.passwordForm.password }
        );
        this.passwordDialogVisible = false;
        ElMessage.success("密码已更新");
      } catch (error) {
        ElMessage.error(error?.response?.data?.detail || "修改密码失败");
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
        ElMessage.warning("开启压缩时必须设置压缩率");
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
        ElMessage.success("上传设置已保存");
        await this.loadUsers();
      } catch (error) {
        ElMessage.error(error?.response?.data?.detail || "保存上传设置失败");
      } finally {
        this.adminLoading = false;
      }
    },

    async init() {
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
}).use(ElementPlus).mount("#app");
