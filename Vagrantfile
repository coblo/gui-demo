Vagrant.configure("2") do |config|

  config.vm.provider "virtualbox" do |v|
    v.gui = true
    v.memory = 4096
  end


  config.vm.define "mac" do |mac|
 	  mac.vm.box = "jhcook/macos-sierra"
  end

  config.vm.define "win" do |win|
	  win.vm.box = "Microsoft/EdgeOnWindows10"
	  win.vm.box_version = "1.0"
	  win.ssh.username = "IEUser"
	  win.ssh.password = "Passw0rd!"
  end

end
